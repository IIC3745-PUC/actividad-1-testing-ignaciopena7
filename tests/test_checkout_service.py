import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError
from src.checkout import CheckoutService, ChargeResult

class TestCheckoutService(unittest.TestCase):

	# Creo la clase CheckoutService antes de probar las funciones de la clase.
	# Coloco las dependencias de la clase como mocks.
	def setUp(self):
		self.payment_gateway = Mock()
		self.email_service = Mock()
		self.fraud_service = Mock()
		self.order_repository = Mock()
		self.pricing_service = Mock()

		self.checkout_service = CheckoutService(
			payments=self.payment_gateway,
			email=self.email_service,
			fraud=self.fraud_service,
			repo=self.order_repository,
			pricing=self.pricing_service
		)


	# Test para checkout
	def test_checkout_invalid_user(self):
		result = self.checkout_service.checkout("   ", [], "token", "CL")
		self.assertEqual(result, "INVALID_USER")

	def test_checkout_pricing_error(self):
		self.pricing_service.total_cents.side_effect = PricingError("test error")
		result = self.checkout_service.checkout("user1", [], "token", "CL")
		self.assertEqual(result, "INVALID_CART:test error")
		self.pricing_service.total_cents.assert_called_once()

	def test_checkout_fraud_rejected(self):
		self.pricing_service.total_cents.return_value = 10000
		self.fraud_service.score.return_value = 85
		
		result = self.checkout_service.checkout("user1", [], "token", "CL")
		
		self.assertEqual(result, "REJECTED_FRAUD")
		self.fraud_service.score.assert_called_once_with("user1", 10000)
		self.payment_gateway.charge.assert_not_called()

	def test_checkout_payment_failed(self):
		self.pricing_service.total_cents.return_value = 10000
		self.fraud_service.score.return_value = 10
		
		charge_result = ChargeResult(ok=False, reason="Insufficient funds")
		self.payment_gateway.charge.return_value = charge_result
		
		result = self.checkout_service.checkout("user1", [], "token", "CL")
		
		self.assertEqual(result, "PAYMENT_FAILED:Insufficient funds")
		self.payment_gateway.charge.assert_called_once_with(user_id="user1", amount_cents=10000, payment_token="token")
		self.order_repository.save.assert_not_called()

	def test_checkout_success(self):
		self.pricing_service.total_cents.return_value = 10000
		self.fraud_service.score.return_value = 10
		
		charge_result = ChargeResult(ok=True, charge_id="charge123")
		self.payment_gateway.charge.return_value = charge_result
		
		result = self.checkout_service.checkout("user1", [], "token", "CL", "SAVE10")
		
		self.assertTrue(result.startswith("OK:"))
		order_id = result.split(":")[1]
		
		# Se verifica que se haya guardado la orden
		self.order_repository.save.assert_called_once()
		saved_order = self.order_repository.save.call_args[0][0]
		self.assertEqual(saved_order.order_id, order_id)
		self.assertEqual(saved_order.user_id, "user1")
		self.assertEqual(saved_order.total_cents, 10000)
		self.assertEqual(saved_order.payment_charge_id, "charge123")
		self.assertEqual(saved_order.coupon_code, "SAVE10")
		self.assertEqual(saved_order.country, "CL")
		
		# Se verifica que se haya enviado el correo
		self.email_service.send_receipt.assert_called_once_with("user1", order_id, 10000)

	def test_checkout_success_no_charge_id(self):
		self.pricing_service.total_cents.return_value = 10000
		self.fraud_service.score.return_value = 10
		
		charge_result = ChargeResult(ok=True, charge_id=None)
		self.payment_gateway.charge.return_value = charge_result
		
		result = self.checkout_service.checkout("user1", [], "token", "CL", "SAVE10")
		
		self.assertTrue(result.startswith("OK:"))
		
		# Se verifica que se haya guardado la orden con UNKNOWN charge id
		self.order_repository.save.assert_called_once()
		saved_order = self.order_repository.save.call_args[0][0]
		self.assertEqual(saved_order.payment_charge_id, "UNKNOWN")
