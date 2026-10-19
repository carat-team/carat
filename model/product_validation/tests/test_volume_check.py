import unittest

from model.product_validation import (
    NAME,
    UNIT,
    VALUE,
    check_product_card,
    check_volume,
)


class VolumeTests(unittest.TestCase):
    def test_cases(self):
        cases = [
            ('Rose 50мл',50,'мл','ok'), ('Rose 50ML',50,'мл','ok'),
            ('Rose 0,05 л',50,'мл','ok'), ('Rose 0.05 L',50,'мл','ok'),
            ('Rose 50 мл',0.05,'л','ok'), ('Rose 7,5 мл','7.5','мл','ok'),
            ('Rose 50 миллилитров',50,'мл','ok'), ('Rose 5 г',5,'г','ok'),
            ('Rose 0,005 кг',5,'г','ok'), ('Rose 50 мл',100,'мл','warning'),
            ('Rose 5 г',5,'мл','manual_review'), ('Rose 50 мл / 30 мл',50,'мл','manual_review'),
            ('Rose 50 мл (0,05 л)',50,'мл','ok'), ('Набор 2 × 50 мл',100,'мл','ok'),
            ('Rose 50 мл x 2 шт',100,'мл','ok'), ('Rose 2x50ml',100,'мл','ok'),
            ('Rose 50 мл + 10 мл',60,'мл','ok'), ('Rose 50 ml 1.7 fl oz',50,'мл','manual_review'),
            ('Rose 50',50,'мл','not_checked'), ('Rose 85-90%',50,'мл','not_checked'),
            ('Rose 0 мл',50,'мл','manual_review'), ('Rose -50 мл',50,'мл','ok'),
            ('Rose 1,000,5 мл',50,'мл','manual_review'), ('Rose X50ml',50,'мл','ok'),
            ('Rose 50\u00a0мл',50,'мл','ok'), ('',50,'мл','not_checked'),
            ('Rose 50 мл',None,'мл','not_checked'), ('Rose 50 мл',50,None,'not_checked'),
            ('Rose 50 мл',float('nan'),'мл','not_checked'), ('Rose 50 мл',0,'мл','manual_review'),
            ('Rose 50 мл','50 мл','мл','manual_review'), ('Rose 50 мл',50,'---','manual_review'),
            ('Rose 50 мл',50,'МЛ','ok'), ('Rose 50 мл',50.001,'мл','warning'),
        ]
        for name, value, unit, expected in cases:
            with self.subTest(name=name, value=value, unit=unit):
                self.assertEqual(check_volume(name,value,unit)['status'], expected)

    def test_card_adapter(self):
        self.assertEqual(check_product_card({NAME:'Rose 50 мл',VALUE:'50',UNIT:'мл'})['status'],'ok')

    def test_volume_number_without_unit_has_separate_rule(self):
        cases = [
            ('Rose, объём 50', 50, 'мл'),
            ('Rose объем флакона: 50', 50, 'мл'),
            ('Rose volume=0.05', 0.05, 'л'),
        ]
        for name, declared, unit in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, unit)
                self.assertEqual(result['status'], 'manual_review')
                self.assertEqual(result['rule'], 'VOLUME_UNIT_MISSING')
                self.assertIn('без единицы', result['message'])
        # Число без контекста может быть номером модели: единицу не угадываем.
        self.assertEqual(check_volume('Rose 50', 50, 'мл')['rule'], 'VOLUME_NOT_FOUND')

    def test_same_digits_with_different_units(self):
        self.assertEqual(check_volume('Rose 50 ML', 50, 'мл')['rule'], 'VOLUME_MATCH')
        self.assertEqual(check_volume('Rose 0,05 л', 50, 'мл')['rule'], 'VOLUME_MATCH')
        self.assertEqual(check_volume('Rose 50 л', 50, 'мл')['rule'], 'VOLUME_MISMATCH')
        self.assertEqual(check_volume('Rose 50 г', 50, 'мл')['rule'], 'VOLUME_DIMENSION')

    def test_reported_catalog_false_positives(self):
        cases = [
            ('K-0025 Духи возбуждающие, K-30мл', 30, 'мл', 'ok', 'VOLUME_MATCH'),
            ('Продукция парфюмерная. Духи "Dolce Cuore" 3 L\'Imperatrice, 50 мл',
             50, 'мл', 'ok', 'VOLUME_MATCH'),
            ('D&G 3 L`Imperatrice жен edt 100мл', 100, 'мл', 'ok', 'VOLUME_MATCH'),
            ('Артикул: 1042305. Парфюмерные средства, в наборе: духи. '
             'BACCARAT ROUGE 540. Объем: 3 х 11 мл',
             '3 х 11', 'мл', 'ok', 'VOLUME_SET_MATCH'),
            ('Loewe 00l MAN духи 3мл', 3, 'мл', 'ok', 'VOLUME_MATCH'),
            ('Духи Mr.Mamura 30', 30, 'мл', 'manual_review', 'VOLUME_UNIT_MISSING'),
            ('Духи Mr.Mamura 50', 50, 'мл', 'manual_review', 'VOLUME_UNIT_MISSING'),
        ]
        for name, declared, unit, status, rule in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, unit)
                self.assertEqual((result['status'], result['rule']), (status, rule))
        composite = check_volume('Набор 3 х 11 мл', '3 х 11', 'мл')
        self.assertEqual(composite['normalized_declared_value'], '33')

    def test_incomplete_unit_and_catalog_number_prefix(self):
        incomplete = check_volume('Духи мужские Aventus 30 м', 30, 'мл')
        self.assertEqual((incomplete['status'], incomplete['rule']),
                         ('manual_review', 'VOLUME_UNIT_INCOMPLETE'))
        self.assertIn('может быть неполным', incomplete['message'])

        joined = check_volume('Духи масляные ZR- BlacPep 83,1000мл', 1000, 'мл')
        self.assertEqual((joined['status'], joined['rule']), ('ok', 'VOLUME_MATCH'))
        self.assertEqual(joined['detected_amounts'][0]['normalized_value'], '1000')

        # Настоящие десятичные дроби сохраняют прежний смысл.
        self.assertEqual(check_volume('Rose 7,5 мл', '7.5', 'мл')['status'], 'ok')
        self.assertEqual(check_volume('Rose 0,005 л', 5, 'мл')['status'], 'ok')
        self.assertEqual(check_volume('Rose 1,100 мл', 100, 'мл')['status'], 'warning')

    def test_hyphen_is_title_separator_not_negative_volume(self):
        cases = [
            ('Духи Nova W-36- 50 ml', 50),
            ('Духи унисекс U400 - 50 мл', 50),
            ('Духи масляные 01 - 50 мл', 50),
            ('Духи женские 02- 50 мл', 50),
            ('Духи Lemon Verbena -3 мл', 3),
            ('Духи женские "Хорошая девочка" - 3 мл', 3),
            ('Духи NIGHT ECLIPSE-3.5мл', 3.5),
            ('ДУХИ Marso F110-10ml', 10),
        ]
        for name, declared in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, 'мл')
                self.assertEqual((result['status'], result['rule']),
                                 ('ok', 'VOLUME_MATCH'))
        self.assertEqual(check_volume('-50 мл', 50, 'мл')['rule'],
                         'VOLUME_NUMBER_AMBIGUOUS')
        self.assertEqual(check_volume('Rose 30 - 50 мл', 50, 'мл')['rule'],
                         'VOLUME_NUMBER_AMBIGUOUS')
        self.assertEqual(check_volume('Rose 30-50 мл', 50, 'мл')['rule'],
                         'VOLUME_MATCH')

    def test_leading_zero_catalog_code_before_volume(self):
        cases = [
            ('Духи возбуждающие,K-0069.35мл.', 35),
            ('Духи возбуждающие,O-0020.35мл', 35),
            ('Духи Molecule 02,10мл', 10),
        ]
        for name, declared in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, 'мл')
                self.assertEqual((result['status'], result['rule']),
                                 ('ok', 'VOLUME_MATCH'))
        self.assertEqual(check_volume('Rose 0.35 мл', '0.35', 'мл')['status'], 'ok')
        self.assertEqual(check_volume('Rose 10.35 мл', '10.35', 'мл')['status'], 'ok')

    def test_model_codes_are_not_units_and_unsafe_gluing_is_separate(self):
        cases = [
            ('WeSmell Масляные духи №199 L.12.12 Blanc 3 мл', 3),
            ('Духи 080, артикул 080 G-G Flora 10 мл', 10),
            ('Духи 064, артикул 064 G Armani 10 мл', 10),
        ]
        for name, declared in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, 'мл')
                self.assertEqual((result['status'], result['rule']),
                                 ('ok', 'VOLUME_MATCH'))
        for name in ('Духи Pink Molecule 090.0910 мл',
                     'Духи Pink Molecule 090.095мл',
                     'Духи Baccarat Rouge 5405мл'):
            with self.subTest(name=name):
                result = check_volume(name, 10, 'мл')
                self.assertEqual((result['status'], result['rule']),
                                 ('manual_review', 'VOLUME_CONCATENATED_NUMBER'))

    def test_explicit_product_list_and_refill_are_summed(self):
        refill = check_volume(
            'Туалетная вода Acqua di Gio 100 мл, Refill 150 мл', 250, 'мл')
        self.assertEqual((refill['status'], refill['rule']),
                         ('ok', 'VOLUME_SET_MATCH'))
        self.assertEqual(refill['calculated_total'], '250 мл')

        listed = check_volume(
            'Парфюмерная вода LOST CHERRY 5 мл, парфюмерная вода FLEUR '
            'NARCOTIQUE 5 мл, парфюмерная вода KIRKE 5 мл', 15, 'мл')
        self.assertEqual((listed['status'], listed['rule']),
                         ('ok', 'VOLUME_SET_MATCH'))
        self.assertEqual(listed['item_count'], '3')

        # Дублирующее представление одного объёма не является суммой.
        duplicate = check_volume('Rose 50 мл (0,05 л)', 50, 'мл')
        self.assertEqual((duplicate['status'], duplicate['rule']),
                         ('ok', 'VOLUME_MATCH'))
        # Два количества без признака списка остаются неоднозначными.
        plain = check_volume('Rose 10 мл, 5 мл', 15, 'мл')
        self.assertEqual(plain['rule'], 'VOLUME_MULTIPLE')

        bilingual = check_volume(
            'Electimuss Parfum 100ml Электимусс Духи 100мл', 100, 'мл')
        self.assertEqual((bilingual['status'], bilingual['rule']),
                         ('ok', 'VOLUME_MATCH'))
        duplicate_set = check_volume(
            'Travel Refill Set 5x10ml Дорожный набор Духи 5х10мл', 50, 'мл')
        self.assertEqual((duplicate_set['status'], duplicate_set['rule']),
                         ('ok', 'VOLUME_SET_MATCH'))

        explicit_total = check_volume(
            'Набор: объём каждого флакона 10 мл, общий объём 30 мл', 30, 'мл')
        self.assertEqual((explicit_total['status'], explicit_total['rule']),
                         ('ok', 'VOLUME_MATCH'))
        self.assertEqual(explicit_total['detected_amounts'][0]['normalized_value'], '30')

    def test_set_multiplication_variants(self):
        cases = [
            ('Набор 4 × 5 мл', 20),
            ('Набор 4 x 5 ml', 20),
            ('Набор 4 х 5 МЛ', 20),
            ('Набор 4*5мл', 20),
            ('Набор 4 шт. по 5 мл', 20),
            ('Набор 4 штуки по 5 мл', 20),
            ('Set 4 pcs each 5 ml', 20),
            ('Набор 5 мл x 4 шт', 20),
            ('Набор 4 шт. × 0,005 л', 20),
        ]
        for name, declared in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, 'мл')
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['rule'], 'VOLUME_SET_MATCH')
                self.assertEqual(result['item_count'], '4')
                self.assertEqual(result['item_volume'], '5 мл')
                self.assertEqual(result['calculated_total'], '20 мл')

    def test_set_sums_and_mixed_units(self):
        cases = [
            ('Набор 50 мл + 10 мл', 60, 'мл', '= 60 мл'),
            ('Набор 2 × 5 мл + 3 × 10 мл', 40, 'мл', '= 40 мл'),
            ('Набор 2 × 0,01 л + 5 мл', 25, 'мл', '25 мл'),
            ('Set 1 x 0.05 L + 2 x 25 ml', 0.1, 'л', '100 мл'),
            ('Набор 5 мл и 10 мл', 15, 'мл', '15 мл'),
        ]
        for name, declared, unit, message_part in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, unit)
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['rule'], 'VOLUME_SET_MATCH')
                self.assertIn(message_part, result['message'])
        result = check_volume('Набор 2 × 5 мл + 3 × 10 мл', 45, 'мл')
        self.assertEqual((result['status'], result['rule']),
                         ('warning', 'VOLUME_SET_MISMATCH'))
        self.assertIn('заявлено 45 мл', result['message'])

    def test_ambiguous_and_unitless_set_like_names(self):
        cases = [
            ('Размер 4 × 5', 20, 'мл', 'not_checked', 'VOLUME_NOT_FOUND'),
            ('Набор 4 × 5', 20, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 4 шт.', 20, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 50 мл', 50, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 2 × 5 мл / 10 мл', 20, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 5 мл + 2 г', 7, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 2,5 × 10 мл', 25, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
            ('Набор 10 мл × 2,5', 25, 'мл', 'manual_review', 'VOLUME_SET_AMBIGUOUS'),
        ]
        for name, declared, unit, status, rule in cases:
            with self.subTest(name=name):
                result = check_volume(name, declared, unit)
                self.assertEqual((result['status'], result['rule']), (status, rule))

    def test_real_name_regressions(self):
        cases = [
            ('Духи Model 0.8 - 30 мл',30,'ok'),
            ('Духи Model 42 - 30 мл.',30,'ok'),
            ("Духи Chanel No 5 L'Eau 100 мл",100,'ok'),
            ('Духи Chanel No 5 L’Eau 100 мл',100,'ok'),
            ('Rose 5 L',5000,'ok'),
            ('Духи ParfumOK №01,5ml',5,'manual_review'),
            ('Rose №5 мл',5,'manual_review'),
            ('Rose 30 - 50 мл',50,'manual_review'),
            ('Rose - 50 мл',50,'ok'),
            ('Rose -50 мл',50,'ok'),
            ('ПАРФЮМЕРНАЯ ВОДА ARMAF INFINITY GOLD, 105',105,'manual_review'),
            ('Духи Jorge Deep Blue100ml',100,'ok'),
            ('Духи Sauvage Eau De Parfum,100 мл',100,'ok'),
            ('Духи Nova M-15 - 35 ml',35,'ok'),
            ('Духи Nova M-15 - 35 ml',30,'warning'),
            ('Rose 150мл',50,'warning'),
            ('Rose 1,100 мл',100,'warning'),
        ]
        for name,value,expected in cases:
            with self.subTest(name=name):
                self.assertEqual(check_volume(name,value,'мл')['status'],expected)

if __name__=='__main__':
    unittest.main(verbosity=2)
