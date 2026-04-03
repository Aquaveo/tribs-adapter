depths = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm']
soil_vars = ['sand', 'silt', 'clay', 'bdod', 'wv0033', 'wv1500']  # note order is important for processing data
type_dict = {
    'sand': "sand_fraction",
    'silt': "silt_fraction",
    'clay': "clay_fraction",
    'bdod': "bulk_density",
    'wv0033': "vwc_33",
    'wv1500': "vwc_1500"
}
tribs_vars = ['Ks', 'theta_r', 'theta_s', 'psib', 'm']
soil_table_parameters = ['ID', 'Ks', 'thetaS', 'thetaR', 'm', 'PsiB', 'f', 'As', 'Au', 'n', 'ks', 'Cs', 'Texture']
