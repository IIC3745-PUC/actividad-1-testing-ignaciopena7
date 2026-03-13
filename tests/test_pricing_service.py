import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError

class TestPricingService(unittest.TestCase):

	# Creo la clase PricingService antes de probar las funciones de la clase.
	def setUp(self):
		self.pricing_service = PricingService()


	# Test para subtotal_cents
	def test_subtotal_cents_empty(self):
		self.assertEqual(self.pricing_service.subtotal_cents([]), 0)

	def test_subtotal_cents_valid(self):
		items = [CartItem("A", 100, 2), CartItem("B", 50, 1)]
		self.assertEqual(self.pricing_service.subtotal_cents(items), 250)

	def test_subtotal_cents_qty_zero(self):
		items = [CartItem("A", 100, 0)]
		with self.assertRaisesRegex(PricingError, "qty must be > 0"):
			self.pricing_service.subtotal_cents(items)

		items = [CartItem("A", 100, -1)]
		with self.assertRaisesRegex(PricingError, "qty must be > 0"):
			self.pricing_service.subtotal_cents(items)

	def test_subtotal_cents_price_negative(self):
		items = [CartItem("A", -10, 1)]
		with self.assertRaisesRegex(PricingError, "unit_price_cents must be >= 0"):
			self.pricing_service.subtotal_cents(items)


	# Test para apply_coupon
	def test_apply_coupon_none_or_empty(self):
		self.assertEqual(self.pricing_service.apply_coupon(1000, None), 1000)
		self.assertEqual(self.pricing_service.apply_coupon(1000, ""), 1000)
		self.assertEqual(self.pricing_service.apply_coupon(1000, "   "), 1000)

	def test_apply_coupon_save10(self):
		self.assertEqual(self.pricing_service.apply_coupon(1000, "SAVE10"), 900)
		self.assertEqual(self.pricing_service.apply_coupon(1000, " save10 "), 900)

	def test_apply_coupon_clp2000_above_zero(self):
		self.assertEqual(self.pricing_service.apply_coupon(3000, "CLP2000"), 1000)

	def test_apply_coupon_clp2000_below_zero(self):
		self.assertEqual(self.pricing_service.apply_coupon(1000, "CLP2000"), 0)

	def test_apply_coupon_invalid(self):
		with self.assertRaisesRegex(PricingError, "invalid coupon"):
			self.pricing_service.apply_coupon(1000, "INVALID")


	# Test para tax_cents
	def test_tax_cents_cl(self):
		self.assertEqual(self.pricing_service.tax_cents(1000, "CL"), 190)

	def test_tax_cents_eu(self):
		self.assertEqual(self.pricing_service.tax_cents(1000, "EU"), 210)

	def test_tax_cents_us(self):
		self.assertEqual(self.pricing_service.tax_cents(1000, "US"), 0)

	def test_tax_cents_invalid(self):
		with self.assertRaisesRegex(PricingError, "unsupported country"):
			self.pricing_service.tax_cents(1000, "AR")


	# Test para shipping_cents
	def test_shipping_cents_cl_free(self):
		self.assertEqual(self.pricing_service.shipping_cents(20000, "CL"), 0)
		self.assertEqual(self.pricing_service.shipping_cents(20001, "CL"), 0)

	def test_shipping_cents_cl_paid(self):
		self.assertEqual(self.pricing_service.shipping_cents(19999, "CL"), 2500)

	def test_shipping_cents_us(self):
		self.assertEqual(self.pricing_service.shipping_cents(1000, "US"), 5000)

	def test_shipping_cents_eu(self):
		self.assertEqual(self.pricing_service.shipping_cents(1000, "EU"), 5000)

	def test_shipping_cents_invalid(self):
		with self.assertRaisesRegex(PricingError, "unsupported country"):
			self.pricing_service.shipping_cents(1000, "AR")


	# Test para total_cents
	def test_total_cents(self):
		items = [CartItem("A", 10000, 2), CartItem("B", 5000, 1)]
		total = self.pricing_service.total_cents(items, "SAVE10", "CL")
		self.assertEqual(total, 26775)

	def test_total_cents_no_coupon(self):
		items = [CartItem("A", 10000, 2), CartItem("B", 5000, 1)]
		total = self.pricing_service.total_cents(items, None, "CL")
		self.assertEqual(total, 29750)
	
	def test_total_cents_clp2000(self):
		items = [CartItem("A", 10000, 2), CartItem("B", 5000, 1)]
		total = self.pricing_service.total_cents(items, "CLP2000", "CL")
		self.assertEqual(total, 27370)
	
	def test_total_cents_invalid_coupon(self):
		items = [CartItem("A", 10000, 2), CartItem("B", 5000, 1)]
		with self.assertRaisesRegex(PricingError, "invalid coupon"):
			self.pricing_service.total_cents(items, "INVALID", "CL")
	
	def test_total_cents_invalid_country(self):
		items = [CartItem("A", 10000, 2), CartItem("B", 5000, 1)]
		with self.assertRaisesRegex(PricingError, "unsupported country"):
			self.pricing_service.total_cents(items, "SAVE10", "AR")
	
	def test_total_cents_empty_items(self):
		items = []
		total = self.pricing_service.total_cents(items, "SAVE10", "CL")
		self.assertEqual(total, 2500)
	
	def test_total_cents_zero_qty(self):
		items = [CartItem("A", 10000, 0)]
		with self.assertRaisesRegex(PricingError, "qty must be > 0"):
			self.pricing_service.total_cents(items, "SAVE10", "CL")

	def test_total_cents_negative_price(self):
		items = [CartItem("A", -10000, 2)]
		with self.assertRaisesRegex(PricingError, "unit_price_cents must be >= 0"):
			self.pricing_service.total_cents(items, "SAVE10", "CL")
