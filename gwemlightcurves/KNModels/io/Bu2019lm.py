# https://arxiv.org/abs/1705.07084

import os, sys, glob, pickle
import numpy as np
import scipy.interpolate
from scipy.interpolate import interpolate as interp
from scipy.interpolate import griddata

from .model import register_model
from .. import KNTable

from gwemlightcurves import lightcurve_utils, Global, svd_utils
from gwemlightcurves.EjectaFits.DiUj2017 import calc_meje, calc_vej

try:
    from tensorflow.keras.models import load_model
except:
    print('Install tensorflow if you want to use it...')

def get_Bu2019lm_model(table, **kwargs):

    if 'LoadModel' in kwargs: 
        LoadModel = kwargs['LoadModel']
    else:
        LoadModel = False

    if 'SaveModel' in kwargs:
        SaveModel = kwargs['SaveModel']
    else:
        SaveModel = False

    if 'ModelPath' in kwargs:
        ModelPath = kwargs['ModelPath']

    if 'doAB' in kwargs:
        doAB = kwargs['doAB']
    else:
        doAB = True

    if 'doSpec' in kwargs:
        doSpec = kwargs['doSpec']
    else:
        doSpec = False

    if not 'n_coeff' in table.colnames:
        if doAB:
            #table['n_coeff'] = 43
            table['n_coeff'] = 10
        elif doSpec:
            table['n_coeff'] = 21

    if not 'gptype' in table.colnames:
        table['gptype'] = 'sklearn'

    if doAB:
        if not Global.svd_mag_model == 0:
            svd_mag_model = Global.svd_mag_model
        else:
            if np.all(table['gptype'] == "sklearn"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_mag.pkl')
            elif np.all(table['gptype'] == "gpytorch"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_mag_gpy.pkl')
            elif np.all(table['gptype'] == "gp_api"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_mag_gpapi.pkl')
            elif np.all(table['gptype'] == "tensorflow"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_mag_tf.pkl')
            if LoadModel:
            #if True:
                with open(modelfile, 'rb') as handle:
                    svd_mag_model = pickle.load(handle)

                if np.all(table['gptype'] == "tensorflow"):
                    outdir = modelfile.replace(".pkl","")
                    for filt in svd_mag_model.keys():
                        outfile = os.path.join(outdir, f'{filt}.h5')
                        svd_mag_model[filt]['model'] = load_model(outfile)

            else:
                svd_mag_model = svd_utils.calc_svd_mag(table['tini'][0], table['tmax'][0], table['dt'][0], model = "Bu2019lm", n_coeff = table['n_coeff'][0], gptype=table['gptype'])

                if np.all(table['gptype'] == "tensorflow"):
                    outdir = modelfile.replace(".pkl","")
                    if not os.path.isdir(outdir):
                        os.makedirs(outdir)
                    for filt in svd_mag_model.keys():
                        outfile = os.path.join(outdir, f'{filt}.h5')
                        svd_mag_model[filt]['model'].save(outfile)
                        del svd_mag_model[filt]['model']

                with open(modelfile, 'wb') as handle:
                    pickle.dump(svd_mag_model, handle, protocol=pickle.HIGHEST_PROTOCOL)

                if np.all(table['gptype'] == "tensorflow"):
                    for filt in svd_mag_model.keys():
                        outfile = os.path.join(outdir, f'{filt}.h5')
                        svd_mag_model[filt]['model'] = load_model(outfile)

            if np.all(table['gptype'] == "gp_api"):
                for filt in svd_mag_model.keys():
                    for ii in range(len(svd_mag_model[filt]["gps"])):
                        svd_mag_model[filt]["gps"][ii] = svd_utils.load_gpapi(svd_mag_model[filt]["gps"][ii])
            Global.svd_mag_model = svd_mag_model

        if not Global.svd_lbol_model == 0:
            svd_lbol_model = Global.svd_lbol_model
        else:
            if np.all(table['gptype'] == "sklearn"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_lbol.pkl')
            elif np.all(table['gptype'] == "gpytorch"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_lbol_gpy.pkl')
            elif np.all(table['gptype'] == "gp_api"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_lbol_gpapi.pkl')
            elif np.all(table['gptype'] == "tensorflow"):
                modelfile = os.path.join(ModelPath,'Bu2019lm_lbol_tf.pkl')
            if LoadModel:
            #if True:

                with open(modelfile, 'rb') as handle:
                    svd_lbol_model = pickle.load(handle)

                if np.all(table['gptype'] == "tensorflow"):
                    outdir = modelfile.replace(".pkl","")
                    outfile = os.path.join(outdir, 'model.h5')
                    svd_lbol_model['model'] = load_model(outfile)
 
            else:
                svd_lbol_model = svd_utils.calc_svd_lbol(table['tini'][0], table['tmax'][0], table['dt'][0], model = "Bu2019lm", n_coeff = table['n_coeff'][0], gptype=table['gptype'])

                if np.all(table['gptype'] == "tensorflow"):
                    outdir = modelfile.replace(".pkl","")
                    if not os.path.isdir(outdir):
                        os.makedirs(outdir)
                    outfile = os.path.join(outdir, 'model.h5')
                    svd_lbol_model['model'].save(outfile)
                    del svd_lbol_model['model']

                with open(modelfile, 'wb') as handle:
                    pickle.dump(svd_lbol_model, handle, protocol=pickle.HIGHEST_PROTOCOL)

                if np.all(table['gptype'] == "tensorflow"):
                    svd_lbol_model['model'] = load_model(outfile)

            if np.all(table['gptype'] == "gp_api"):
                for ii in range(len(svd_lbol_model["gps"])):
                    svd_lbol_model["gps"][ii] = svd_utils.load_gpapi(svd_lbol_model["gps"][ii])

            Global.svd_lbol_model = svd_lbol_model
    elif doSpec:
        if not Global.svd_spec_model == 0:
            svd_spec_model = Global.svd_spec_model
        else:
            if LoadModel:
            #if True:
                modelfile = os.path.join(ModelPath,'Bu2019lm_spec.pkl')
                with open(modelfile, 'rb') as handle:
                    svd_spec_model = pickle.load(handle)
            else:
                svd_spec_model = svd_utils.calc_svd_spectra(table['tini'][0], table['tmax'][0], table['dt'][0], table['lambdaini'][0], table['lambdamax'][0], table['dlambda'][0], model = "Bu2019lm", n_coeff = table['n_coeff'][0])
                modelfile = os.path.join(ModelPath,'Bu2019lm_spec.pkl')
                with open(modelfile, 'wb') as handle:
                    pickle.dump(svd_spec_model, handle, protocol=pickle.HIGHEST_PROTOCOL)
            Global.svd_spec_model = svd_spec_model

    if not 'mej_dyn' in table.colnames:
        # calc the mass of ejecta
        table['mej_dyn'] = calc_meje(table['m1'], table['mb1'], table['c1'], table['m2'], table['mb2'], table['c2'])
        # calc the velocity of ejecta
        table['vej'] = calc_vej(table['m1'], table['c1'], table['m2'], table['c2'])

    # Throw out smaples where the mass ejecta is less than zero.
    mask = (table['mej_dyn'] > 0)
    table = table[mask]
    if len(table) == 0: return table

    # Log mass ejecta
    table['mej_dyn10'] = np.log10(table['mej_dyn'])
    table['mej_wind10'] = np.log10(table['mej_wind'])
    # Initialize lightcurve values in table

    timeseries = np.arange(table['tini'][0], table['tmax'][0]+table['dt'][0], table['dt'][0])
    table['t'] = [np.zeros(timeseries.size)]
    if doAB:
        table['lbol'] = [np.zeros(timeseries.size)]
        table['mag'] =  [np.zeros([9, timeseries.size])]
    elif doSpec:
        lambdas = np.arange(table['lambdaini'][0], table['lambdamax'][0]+table['dlambda'][0], table['dlambda'][0])
        table['lambda'] = [np.zeros(lambdas.size)]
        table['spec'] =  [np.zeros([lambdas.size, timeseries.size])]

    # calc lightcurve for each sample
    for isample in range(len(table)):
        print(np.log10(table['mej_dyn'][isample]),np.log10(table['mej_wind'][isample]),table['phi'][isample],table['theta'][isample])

        print('Generating sample %d/%d' % (isample, len(table)))
        if doAB:
            table['t'][isample], table['lbol'][isample], table['mag'][isample] = svd_utils.calc_lc(table['tini'][isample], table['tmax'][isample],table['dt'][isample], [np.log10(table['mej_dyn'][isample]),np.log10(table['mej_wind'][isample]),table['phi'][isample],table['theta'][isample]],svd_mag_model = svd_mag_model, svd_lbol_model = svd_lbol_model, model = "Bu2019lm", gptype=table['gptype'][0])
        elif doSpec:
            table['t'][isample], table['lambda'][isample], table['spec'][isample] = svd_utils.calc_spectra(table['tini'][isample], table['tmax'][isample],table['dt'][isample], table['lambdaini'][isample], table['lambdamax'][isample]+table['dlambda'][isample], table['dlambda'][isample], [np.log10(table['mej_dyn'][isample]),np.log10(table['mej_wind'][isample]),table['phi'][isample],table['theta'][isample]],svd_spec_model = svd_spec_model, model = "Bu2019lm")

    return table

register_model('Bu2019lm', KNTable, get_Bu2019lm_model,
                 usage="table")
