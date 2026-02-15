import pytest
from modules.quote_calculator import calculate_quote, convert_volume, validate_surcharges, load_pricing


class TestVolumeConversion:
    def test_chars(self):
        assert convert_volume(4500, "chars") == 4500

    def test_words(self):
        assert convert_volume(100, "words") == 250

    def test_pages(self):
        assert convert_volume(8, "pages") == 2400

    def test_unknown_unit(self):
        with pytest.raises(ValueError, match="Unknown volume unit"):
            convert_volume(100, "lines")


class TestSurchargeValidation:
    def test_exclusive_surcharges(self):
        pricing = load_pricing()
        with pytest.raises(ValueError, match="mutually exclusive"):
            validate_surcharges(["urgent", "semi_urgent"], pricing)

    def test_unknown_surcharge(self):
        pricing = load_pricing()
        with pytest.raises(ValueError, match="Unknown surcharge"):
            validate_surcharges(["unknown"], pricing)

    def test_valid_combination(self):
        pricing = load_pricing()
        result = validate_surcharges(["urgent", "dtp"], pricing)
        assert result == ["urgent", "dtp"]


class TestCalculateQuote:
    def test_scenario_a(self):
        """테스트 A: 한→영 일반 4,500자 + DTP = 712,800원"""
        result = calculate_quote(
            language_pair="ko-en",
            domain="general",
            volume=4500,
            volume_unit="chars",
            surcharge_keys=["dtp"],
        )
        assert result.converted_chars == 4500
        assert result.unit_price == 120
        assert result.base_amount == 540_000
        assert result.surcharge_total == 108_000
        assert result.subtotal == 648_000
        assert result.vat == 64_800
        assert result.total == 712_800

    def test_scenario_b(self):
        """테스트 B: 한→영 법률 8페이지(=2,400자) + 긴급 = 712,800원"""
        result = calculate_quote(
            language_pair="ko-en",
            domain="legal",
            volume=8,
            volume_unit="pages",
            surcharge_keys=["urgent"],
        )
        assert result.converted_chars == 2400
        assert result.unit_price == 180
        assert result.base_amount == 432_000
        assert result.surcharge_total == 216_000
        assert result.subtotal == 648_000
        assert result.vat == 64_800
        assert result.total == 712_800

    def test_no_surcharge(self):
        result = calculate_quote(
            language_pair="en-ko",
            domain="general",
            volume=1000,
            volume_unit="chars",
        )
        assert result.base_amount == 110_000
        assert result.surcharge_total == 0
        assert result.subtotal == 110_000
        assert result.vat == 11_000
        assert result.total == 121_000

    def test_multiple_surcharges(self):
        """긴급 + DTP 동시 적용"""
        result = calculate_quote(
            language_pair="ko-ja",
            domain="technical",
            volume=1000,
            volume_unit="chars",
            surcharge_keys=["urgent", "dtp"],
        )
        assert result.base_amount == 180_000
        # urgent 50% + dtp 20% = 70%
        assert result.surcharge_total == 126_000
        assert result.subtotal == 306_000
        assert result.vat == 30_600
        assert result.total == 336_600

    def test_invalid_language_pair(self):
        with pytest.raises(ValueError, match="Unknown language pair"):
            calculate_quote("ko-fr", "general", 1000)

    def test_invalid_domain(self):
        with pytest.raises(ValueError, match="Unknown domain"):
            calculate_quote("ko-en", "finance", 1000)

    def test_exclusive_surcharge_error(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            calculate_quote("ko-en", "general", 1000, surcharge_keys=["urgent", "semi_urgent"])
