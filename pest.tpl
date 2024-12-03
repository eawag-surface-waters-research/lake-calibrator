&aed2_models
    models = 'aed2_noncohesive', 'aed2_oxygen', 'aed2_carbon', 'aed2_silica',
             'aed2_nitrogen', 'aed2_phosphorus', 'aed2_organic_matter',
             'aed2_phytoplankton'
/

&aed2_tracer
    retention_time = .true.
    num_tracers = 1
    decay = 0, 0
    fsed = 0, 0
/

&aed2_noncohesive
    num_ss = 1
    ss_initial = 1, 1
    ke_ss = 0.06, 0.063
    settling = 3
    w_ss = -0.03, -0.001
    d_ss = 2e-06, 1e-05
    rho_ss = 1500, 1800
    resuspension = 1
    epsilon = 0.007
    tau_0 = 0.03, 0.03
    tau_r = 1
    ktau_0 = 0.001
/

&aed2_oxygen
    oxy_initial = 225.0
    fsed_oxy = '$$  Fsed_oxy$$'
    ksed_oxy = '$$  Ksed_oxy$$'
    theta_sed_oxy = 1.1
    oxy_min = 0
    oxy_max = 500
    oxy_piston_model = 10
/

&aed2_carbon
    dic_initial = 1600.5
    fsed_dic = 14.0
    ksed_dic = 20.0
    theta_sed_dic = 1.08
    ph_initial = 7.5
    atm_co2 = 0.0004
    ionic = 0.1
    ch4_initial = 27.6
    rch4ox = 0.01
    kch4ox = 0.5
    vtch4ox = 1.08
    fsed_ch4 = 0.5
    ksed_ch4 = 100.0
    theta_sed_ch4 = 1.08
    methane_reactant_variable = 'OXY_oxy'
/

&aed2_silica
    rsi_initial = 100
    fsed_rsi = 50
    ksed_rsi = 50.0
    theta_sed_rsi = 1.08
    silica_reactant_variable = 'OXY_oxy'
/

&aed2_nitrogen
    amm_initial = 0
    nit_initial = 500
    n2o_initial = 500
    rnitrif = 0.01
    knitrif = 80
    theta_nitrif = 1.08
    nitrif_reactant_variable = 'OXY_oxy'
    nitrif_ph_variable = ''
    simnitrfph = .false.
    rnh4o2 = 1
    rno2o2 = 1
    simn2o = 0
    rn2o = 0.05
    kpart_ammox = 1
    kin_deamm = 1
    atm_n2o = 3.2e-07
    n2o_piston_model = 4
    rnh4no2 = 1
    ranammox = 0.001
    kanmx_nit = 2
    kanmx_amm = 2
    rdenit = 0.01
    kdenit = 15.6
    theta_denit = 1.08
    rdnra = 0.01
    kdnra_oxy = 2
    fsed_amm = 0.5
    ksed_amm = 30
    fsed_nit = 0.5
    ksed_nit = 173.1347
    fsed_n2o = 0
    ksed_n2o = 100
    theta_sed_amm = 1.08
    theta_sed_nit = 1.08
    simdrydeposition = .true.
    simwetdeposition = .true.
/

&aed2_phosphorus
    frp_initial = 3.48
    fsed_frp = 0.52
    ksed_frp = 30.0
    theta_sed_frp = 1.08
    phosphorus_reactant_variable = 'OXY_oxy'
    simpo4adsorption = .false.
    ads_use_external_tss = .false.
    po4sorption_target_variable = 'NCS_ss1'
    po4adsorptionmodel = 1
    kpo4p = 0.01
    w_po4ads = -0.01
/

&aed2_organic_matter
    poc_initial = 15
    doc_initial = 15
    pon_initial = 2
    don_initial = 1.1
    pop_initial = 0.1
    dop_initial = 0.01
    docr_initial = 150.0
    donr_initial = 9
    dopr_initial = 0.15
    cpom_initial = 0
    rdom_minerl = 0.01348416
    rpoc_hydrol = 0.001
    rpon_hydrol = 0.001
    rpop_hydrol = 0.0001
    theta_hydrol = 1.07
    theta_minerl = 1.07
    kpom_hydrol = 33.66593
    kdom_minerl = 22.36079
    simdenitrification = 1
    dom_miner_oxy_reactant_var = 'OXY_oxy'
    doc_miner_product_variable = 'CAR_dic'
    don_miner_product_variable = 'NIT_amm'
    dop_miner_product_variable = 'PHS_frp'
    dom_miner_nit_reactant_var = 'NIT_nit'
    f_an = 0.5
    k_nit = 10.0
    simrpools = .true.
    rdomr_minerl = 0.001
    rcpom_bdown = 0.005
    x_cpom_n = 0.005
    x_cpom_p = 0.001
    kedom = 0.03
    kepom = 0.096
    kedomr = 0.15
    kecpom = 0.00096
    simphotolysis = .false.
    photo_c = 0.75
    settling = 1
    w_pom = -0.01
    d_pom = 1e-05
    rho_pom = 1200.0
    w_cpom = -0.01
    d_cpom = 1e-05
    rho_cpom = 1400.0
    resuspension = 1
    resus_link = 'NCS_resus'
    sedimentomfrac = 0.0002
    xsc = 0.5
    xsn = 0.05
    xsp = 0.005
    fsed_doc = 1.4
    fsed_don = 0.0
    fsed_dop = 0.0
    ksed_dom = 93.0
    theta_sed_dom = 1.06
    diag_level = 10
/

&aed2_phytoplankton
    num_phytos = 2
    the_phytos = 1, 2
    settling = 3, 3
    do_mpb = 0
    p_excretion_target_variable = 'OGM_dop'
    n_excretion_target_variable = 'OGM_don'
    c_excretion_target_variable = 'OGM_doc'
    si_excretion_target_variable = ''
    p_mortality_target_variable = 'OGM_pop'
    n_mortality_target_variable = 'OGM_pon'
    c_mortality_target_variable = 'OGM_poc'
    si_mortality_target_variable = ''
    p1_uptake_target_variable = 'PHS_frp'
    n1_uptake_target_variable = 'NIT_amm'
    n2_uptake_target_variable = 'NIT_nit'
    si_uptake_target_variable = 'SIL_rsi'
    do_uptake_target_variable = 'OXY_oxy'
    c_uptake_target_variable = 'CAR_dic'
    dbase = 'aed2/aed2_phyto_pars.nml'
/

&aed2_totals
    tn_vars = 'NIT_nit', 'NIT_amm', 'OGM_don', 'OGM_pon'
    tn_varscale = 1.0, 1.0, 1.0, 1.0, 0.15
    tp_vars = 'PHS_frp', 'PHS_frp_ads', 'OGM_dop', 'OGM_pop'
    tp_varscale = 1.0, 1.0, 1.0, 0.01
/
