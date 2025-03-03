#!/usr/bin/env python

"""generate a KDE for mass ratio conditioned on a chirp mass based on a set of samples
"""

#-------------------------------------------------
import matplotlib
font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 16}
matplotlib.rc('xtick', labelsize=16)
matplotlib.rc('ytick', labelsize=16)
matplotlib.rc('font', **font)
import numpy as np
#from astropy.table import (Table, Column, vstack)
import pickle
#import sys
import os
import scipy.stats as ss
from scipy.stats import rv_continuous
from scipy.integrate import quad
import matplotlib.pyplot as plt
import math
import pandas as pd
import h5py
import bilby
from joblib import Parallel, delayed


### non-standard libraries
from gwemlightcurves.KNModels import KNTable
from gwemlightcurves import __version__
#from gwemlightcurves.EOS.EOS4ParameterPiecewisePolytrope import EOS4ParameterPiecewisePolytrope
#from twixie import kde
from gwemlightcurves import lightcurve_utils
from andrew.mass_grid_fast import run_EOS
#-------------------------------------------------

np.random.seed(0)

'''
The number of points to evaluate the KDE at and plot
'''
#mass_points = 100
mass_points = 10
N_EOS = 100
'''
Determines the number of masses to draw from the inital mass dists, should be >1000. uniform_mass_draws can be
less than mass_draws, as the uniform dists are easier to sample/converge quicker
'''
#mass_draws = 2000
mass_draws = 50

#mass_draws = 20
#uniform_mass_draws = int(mass_draws/2)
uniform_mass_draws = mass_draws

mass = np.linspace(-5, .5, mass_points) 
all_samples = []

def greedy_kde_areas_1d(pts):

    pts = np.random.permutation(pts)
    mu = np.mean(pts, axis=0)

    Npts = pts.shape[0]
    kde_pts = pts[:int(Npts/2)]
    den_pts = pts[int(Npts/2):]

    kde = ss.gaussian_kde(kde_pts.T)

    kdedir = {}
    kdedir["kde"] = kde
    kdedir["mu"] = mu

    return kdedir

def kde_eval(kdedir,truth):

    kde = kdedir["kde"]
    mu = kdedir["mu"]
    L = kdedir["L"]

    truth = np.linalg.solve(L, truth-mu)
    td = kde(truth)

    return td

def kde_eval_single(kdedir,truth):

    kde = kdedir["kde"]
    mu = kdedir["mu"]
    td = kde(truth)

    return td


def alsing_pdf(m):
        mu1, sig1, mu2, sig2, a = 1.34, 0.07, 1.8, 0.21, 2.12
        PDF1 = a/(sig1*np.sqrt(2*np.pi))*np.exp(-((m-mu1)/(np.sqrt(2)*sig1))**2)
        PDF2 = a/(sig2*np.sqrt(2*np.pi))*np.exp(-((m-mu2)/(np.sqrt(2)*sig2))**2)
        PDF = PDF1+PDF2
        return PDF

def farrow_pdf(m):
        mu1, sig1, mu2, sig2, a = 1.34, 0.02, 1.47, 0.15, 0.68
        PDF1 = a/(sig1*np.sqrt(2*np.pi))*np.exp(-((m-mu1)/(np.sqrt(2)*sig1))**2)
        PDF2 = (1-a)/(sig2*np.sqrt(2*np.pi))*np.exp(-((m-mu2)/(np.sqrt(2)*sig2))**2)
        PDF = PDF1+PDF2
        return PDF
    
def zhu_pdf(m):
        a1, a2, a3, b1, b2, b3 = .002845, 1.04e11, 799.1, 1.686, 2.1489, .2904
        PDF = 1/(1/(a1*np.exp(b1*m))+1/(a2*np.exp(-b2*m)+a3*np.exp(-b3*m)))
        return PDF


class alsing_dist(rv_continuous):        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.normalize, _ = quad(alsing_pdf, self.a, self.b)

    def _pdf(self, m):
        return alsing_pdf(m) / self.normalize  

    
class farrow_dist(rv_continuous):        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.normalize, _ = quad(farrow_pdf, self.a, self.b)

    def _pdf(self, m):
        return farrow_pdf(m) / self.normalize  
    

class zhu_dist(rv_continuous):        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.normalize, _ = quad(zhu_pdf, self.a, self.b)

    def _pdf(self, m):
        return zhu_pdf(m) / self.normalize  
    

a_dist = alsing_dist(a=1.1,b=2.8)
f_dist = farrow_dist(a=1.1,b=2.8)
z_dist = zhu_dist(a=2.8,b=25)
ns_astro_mass_dist = ss.norm(1.33, 0.09)
bh_astro_mass_dist = ss.pareto(b=1.3)

def calc_mej_from_masses(i, m1, m2, thetas, Type, Type_set, EOS, all_samples = all_samples):
    '''
    '''
    
    if i%10 == 0:
        print(f'{i} out of {mass_draws} mej values calculated--------------------------')

    #print(f'{i} out of {mass_draws} mej values calculated--------------------------')    

    m1m = m1[i]
    m2m = m2[i]
    
    '''
    m1m_check = m1m
    m2m_check = m2m
    if Type == 'NSBH':
        m1m_check = 1
        m2m_check = .5
    if Type_set == 'BNS_equal':
        m1m = m2m
        m1m_check = m2m
        Type = 'BNS'
    if (m1m_check >= m2m_check) and (m1m_check <= 3):
        print('Initializing '+str(m1m)+' '+str(m2m)+' '+Type_set)

        #parallel_data = (Parallel(n_jobs=N_parallel)(delayed(KNTable.model)(model, s, **kwargs) for s in sample_split))
        samples = run_EOS(EOS, m1m, m2m, chi, thetas, N_EOS = N_EOS, type_set=Type, lan_override = True, lan_override_val = lan)
    '''
    if True:     

        if Type == 'BNS':
            idx = np.where((samples['lambda2'] > 0) | (samples['lambda1'] > 0))[0]
            N_idx = len(idx)
            print('-----------------------------------------------------')
            print(str(N_idx)+' out of '+str(len(samples))+' were BNS')
            print('-----------------------------------------------------')
        if Type == 'NSBH':
            idx = np.where((samples['lambda2'] > 0) | (samples['lambda1'] <= 1e-6))[0]
            N_idx = len(idx)
            print('-----------------------------------------------------')
            print(str(N_idx)+' out of '+str(len(samples))+' were NSBH')
            print('-----------------------------------------------------')

        samples = samples[idx]
         
        mej_samples = np.array(samples['mej'])
        m1_vals = np.array(samples['m1'])
        m2_vals = np.array(samples['m2'])
        mchirp = np.array(samples['mchirp'])
        q = np.array(samples['q'])
        mej = np.array(samples['mej'])
        vej = np.array(samples['vej'])
        dyn_mej = np.array(samples['dyn_mej'])
        wind_mej = np.array(samples['wind_mej'])
        thetas = np.array(samples['theta'])

    return m1_vals, m2_vals, mchirp, q, vej, mej, wind_mej, dyn_mej, thetas



def run_theoretical(Type, lan, chi, EOS, mass_draws=mass_draws):
    '''function to generate mass grid using EOS, should probably be left as is
    '''
    chi_list = [chi]
    #data = []
    Type_set=Type

    if Type == 'Event':

        filename = "./event_files/S190901ap_files/LALInference.v2.posterior_samples.hdf5"


        f = h5py.File(filename, 'r')
        #posterior = f['lalinference']['lalinference_nest']['posterior_samples'][()]
        posterior = f['lalinference']['lalinference_mcmc']['posterior_samples'][()]

        M = bilby.gw.conversion.chirp_mass_and_mass_ratio_to_total_mass(posterior['mc'], posterior['q'])
        m1, m2 = bilby.gw.conversion.total_mass_and_mass_ratio_to_component_masses( posterior['q'], M)

        m1, m2 = m1[:20], m2[:20]
        mass_draws = len(m1)

        print(f'{mass_draws} posterior samples from event')
        Type = 'NSBH'

    all_thetas_list = 180. * np.arccos(np.random.uniform(-1., 1., mass_draws * N_EOS)) / np.pi
    print('len thetas:')
    print(len(all_thetas_list))
    #all_thetas_list = 180. * np.arccos(np.random.uniform(-1., 1., len(samples) * nsamples)) / np.pi

    type_plot = Type
    #-----------------------------------------------------------
    '''
    Determines grid of masses to use for mass grid
    '''
    #----------------------------------------------------------
    if Type == 'NSBH_uniform':
        m2 = 1.1*np.ones(uniform_mass_draws)+1.7*np.random.rand(uniform_mass_draws)
        m1 = 3*np.ones(uniform_mass_draws)+5*np.random.rand(uniform_mass_draws)
        Type = 'NSBH'
    if Type == 'BNS_uniform':
        m1 = 1.1*np.ones(uniform_mass_draws)+1.7*np.random.rand(uniform_mass_draws)
        m2 = 1.1*np.ones(uniform_mass_draws)+1.7*np.random.rand(uniform_mass_draws)
        Type = 'BNS'
    if Type == 'BNS_alsing':
        m_a = a_dist.rvs(size = mass_draws)
        m_b = a_dist.rvs(size = mass_draws)
        m1_list = []
        m2_list = []
        #sort to make sure m1 > m2
        for i in range(len(m_a)):
            if m_a[i] >= m_b[i]:
                m1_list.append(m_a[i])
                m2_list.append(m_b[i])
            else:
                m1_list.append(m_b[i])
                m2_list.append(m_a[i])
        m1 = np.array(m1_list)
        m2 = np.array(m2_list)
        Type = 'BNS' 
    if Type == 'BNS_farrow':

        m_a = f_dist.rvs(size = mass_draws)
        m_b = 1.1*np.ones(mass_draws)+1.7*np.random.rand(mass_draws)
        m1_list = []
        m2_list = []
        #sort to make sure m1 > m2
        for i in range(len(m_a)):
            if m_a[i] >= m_b[i]:
                m1_list.append(m_a[i])
                m2_list.append(m_b[i])
            else:
                m1_list.append(m_b[i])
                m2_list.append(m_a[i])
        m1 = np.array(m1_list)
        m2 = np.array(m2_list)
        Type = 'BNS' 
    if Type == 'NSBH_zhu':

        dist_NS_zhu = ss.norm(1.33, scale = .01)
        m2 = dist_NS_zhu.rvs(mass_draws)
        #m2 = 1.33*np.ones(mass_draws)
        #m2 = a_dist.rvs(size = mass_draws)
        m1 = z_dist.rvs(size = mass_draws)

        Type = 'NSBH'


    if Type == 'BNS_equal_alsing':
        m1 = a_dist.rvs(size = mass_draws)
        m2 = m1
        Type = 'BNS' 
    if Type == 'BNS_equal_farrow':
        m1 = f_dist.rvs(size = mass_draws)
        m2 = m1
        Type = 'BNS'
    if Type == 'NSBH_LRR':
        m1 = bh_astro_mass_dist.rvs(mass_draws)
        m2 = ns_astro_mass_dist.rvs(mass_draws)
        Type = 'NSBH'
    if Type == 'BNS_LRR':
        m1 = ns_astro_mass_dist.rvs(mass_draws)
        m2 = ns_astro_mass_dist.rvs(mass_draws) 
        Type = 'BNS'


    if Type == 'NSBH_zhu_edited':

        #dist_NS_zhu = ss.norm(1.33, scale = .01)
        #m2 = dist_NS_zhu.rvs(mass_draws)
        #m2 = 1.33*np.ones(mass_draws)
        #m2 = a_dist.rvs(size = mass_draws)
        
        #m2 = np.random.normal(1.33, .01, mass_draws)
        #m1 = m2 * np.random.normal(3.6, .01, mass_draws)
        

        m1 = z_dist.rvs(size = mass_draws)
        m2 = m1/(np.random.normal(3.6, .01, mass_draws))

        Type = 'NSBH' 

    if Type == 'NSBH_q_range':

        #dist_NS_zhu = ss.norm(1.33, scale = .01)
        #m2 = dist_NS_zhu.rvs(mass_draws)
        #m2 = 1.33*np.ones(mass_draws)
        #m2 = a_dist.rvs(size = mass_draws)

        m2 = np.random.normal(1.33, .01, mass_draws)
        m1 = m2 * np.random.normal(3.6, .01, mass_draws)


        #m1 = z_dist.rvs(size = mass_draws)
        #m2 = m1/(np.random.normal(3.6, .01, mass_draws))

        Type = 'NSBH'

    if Type == 'NSBH_LRR_edited':
        m1 = bh_astro_mass_dist.rvs(mass_draws)
        #m2 = ns_astro_mass_dist.rvs(mass_draws)
        m2 = m1/(np.random.normal(4.5, .01, mass_draws))
        Type = 'NSBH'


    #--------------------------------------------------------

        
    all_mejs, all_thetas, all_m1s, all_m2s = [],[],[],[]
    all_mchirps, all_qs, all_vejs, all_wind_mejs, all_dyn_mejs = [],[],[],[],[]
    all_lists = [all_mejs, all_thetas, all_m1s, all_m2s, all_mchirps, all_qs, all_vejs, all_wind_mejs, all_dyn_mejs]
        
    N_parallel = 16
    #N_parallel = 1
    print(f'running in parallel on {N_parallel} cores')

    #100 thetas
    all_samples = Parallel(n_jobs = N_parallel)(delayed(calc_mej_from_masses)(i, m1, m2, all_thetas_list[int((i)*N_EOS):int((i+1)*N_EOS)], Type, Type_set, EOS) for i in range(len(m1)))
    #1 theta
    #all_samples = Parallel(n_jobs = N_parallel)(delayed(calc_mej_from_masses)(i, m1, m2, all_thetas_list[int((i-1)):int(i)], Type, Type_set, EOS) for i in range(len(m1)))        
 
    all_samples = np.array(all_samples)
    #print(all_samples.shape)
    #print(all_samples[0][0])
    all_lists = np.array(all_lists)
 
    all_m1s, all_m2s, all_mchirps = all_samples[:,0,:], all_samples[:,1,:], all_samples[:,2,:]
    all_qs, all_vejs, all_mejs = all_samples[:,3,:], all_samples[:,4,:], all_samples[:,5,:]
    all_wind_mejs, all_dyn_mejs, all_thetas = all_samples[:,6,:], all_samples[:,7,:], all_samples[:,8,:]

    # can replace with flatten-- 
    shape1, shape2 = all_m1s.shape
    all_m1s_1D = np.reshape(all_m1s, (shape1*shape2))
    all_m2s_1D = np.reshape(all_m2s, (shape1*shape2))
    all_mchirps_1D = np.reshape(all_mchirps, (shape1*shape2))
    all_qs_1D = np.reshape(all_qs, (shape1*shape2))
    all_vejs_1D = np.reshape(all_vejs, (shape1*shape2))
    all_mejs_1D = np.reshape(all_mejs, (shape1*shape2))
    all_wind_mejs_1D = np.reshape(all_wind_mejs, (shape1*shape2))
    all_dyn_mejs_1D = np.reshape(all_dyn_mejs, (shape1*shape2))
    all_thetas_1D = np.reshape(all_thetas, (shape1*shape2))
  

    plt.figure()
    plt.hist(np.log10(all_mejs_1D), bins = 20, range = (-20, 20))
    plt.yscale('log')
    plt.xlabel('mej')
    plt.ylabel('Probability')
    plt.savefig(f'./output/mej_hist_{type_plot}.pdf')
    plt.close()
    #mean_data=np.array(data)
    id_list = np.arange(0,len(all_mejs_1D))
    mej_theta = np.column_stack((all_mejs_1D, all_thetas_1D, id_list))
    corner_data = np.column_stack((all_m1s_1D, all_m2s_1D, all_mchirps_1D, all_qs_1D, all_vejs_1D, all_mejs_1D, all_wind_mejs_1D, all_dyn_mejs_1D, all_thetas_1D, id_list))
    np.savetxt('./mej_theta_data/NSBH_test/mej_theta_data_'+str(Type_set)+'.txt', mej_theta)
    #np.savetxt('./mej_theta_data/test/mej_theta_data_'+str(Type_set)+'.txt', mej_theta)
    np.savetxt('./corner_data/NSBH_test/corner_data_'+str(Type_set)+'.txt', corner_data)
    return all_mejs



def run_prob(mass, lan, chi, coverage_factors = False, theor = False, Type = None):
    ''' function that uses EOS and generates KDE, the only thing that could be changed here is the EOS type,
        which is now set to gp
    '''
    l = len(mass) 
    prob_events=[]
    prob_norm_events=[] 
    samples=[]
    
    prob_list = []
    prob_norm_list = []
    #----------------------------------------------------------------------
    '''
    EOS determined here, usually we use gp, unlikely this needs to be changed
    '''
    #---------------------------------------------------------------------
    EOS_type = 'gp'
    #EOS_type = 'Sly'
    all_data = run_theoretical(Type, lan, chi, EOS_type)
    shape = np.shape(all_data)
    num = 1
 
    for n in range(len(shape)):
        num = num * shape[n]
               
    all_data = np.reshape(np.array(all_data), (int(num)))
                 

    '''
    deleted checks for now
    '''
    #all_data[all_data > 1e0] = 1e0
    #all_data[all_data <= 1e-6] = 1e-12
                
    all_data = np.log10(all_data)
            
    KDE = greedy_kde_areas_1d(all_data)
        
        
    Nsamples = 1e4
    if Nsamples < 1e3: 
        print('Nsamples may be too small')
    limit = 1
    limit_norm = 1
                
    for i,m in enumerate(mass):
        p_samples = []
        p_norm_samples =[]
        for c in range(int(Nsamples)):
            if not theor:
                prob = kde_eval_single(KDE, 10**m)[0]
                prob_norm = kde_eval_single(KDE, .001)[0]
                prob_norm =1
            if theor: 
                prob = kde_eval_single(KDE, m)[0]
                prob_norm = kde_eval_single(KDE, -3)[0]
                prob_norm =1
            thresh = np.random.uniform(0,1)
            if prob > thresh:
                #p_samples.append(cov[e]*prob)
                p_samples.append(prob)
                #p_norm_samples.append(cov[e]*prob_norm)
                p_norm_samples.append(prob_norm)


            prob_list.append(np.mean(p_samples))
            prob_norm_list.append((np.mean(p_norm_samples)))
        prob_events.append(np.array(prob_list))
        prob_norm_events.append(np.array(prob_norm_list))


        data_out = (all_data)
        mej_test = mass
   
        prob_kde=[]
        for m in mej_test:
            kde_test = kde_eval_single(KDE, m)
            prob_kde.append(kde_test)
        mej_norm = kde_eval_single(KDE, 1e-3)
        mej_norm=1
        prob_kde = np.array(prob_kde)
        prob_kde = prob_kde / np.sum(prob_kde)
        mej_probs = prob_kde

    if theor:
        return mej_probs, mej_norm, mej_test, chi, EOS_type
    if not theor:
        return np.array(prob_events), np.array(prob_norm_events) 


def plot(mass, prob_events, prob_norm_events, lan, chi, coverage_factors=False):
    '''function to plot PDFs and save PDF data to file
    '''

    #if coverage_factors == True:    
        #event_prob = np.array([0.2390, 0.5157, 0.7837, 0.4939, 0.3117, 0.2892, 0.1922, 0.4342, 0.0485, 0.009, 0.4796, 0.1817, 0.7608])


    #event_names = ['GW190425', 'S190426c','GW190814', 'S190901ap', 'S190910d', 'S190910h', 'S190923y', 'S190930t', 'S191205ah', 'S191213g', 'S200105ae', 'S200115j', 'S200213t']
    colors = ['blue', 'gold', 'black', 'dodgerblue', 'firebrick', 'c', 'peru', 'saddlebrown', 'goldenrod', 'indigo', 'r', 'orange', 'blueviolet']
 
    mej_kde = []
    plot_mass = 10**mass
    labels = ['BNS (Alsing et al.)', 'BNS (Farrow et al.)', 'BNS, m1=m2 (Alsing et al.)', 'BNS, m1=m2 (Farrow et al.)',  'BNS, Uniform in m1, m2', 'NSBH, Uniform in m1, m2', 'NSBH (Alsing et al., Zhu et al.)', 'BNS, Uniform in chirp, q']
    labels = ['NSBH (Zhu et al.)', 'NSBH (LRR)'] 
    
    #Types = ['BNS_alsing','BNS_farrow','BNS_equal_alsing','BNS_equal_farrow','BNS_uniform','NSBH_uniform','NSBH_zhu','BNS_chirp_q']
    #Types = ['NSBH_zhu','NSBH_LRR']
    #Types = ['NSBH_zhu_edited', 'NSBH_LRR_edited']
    #Types = ['NSBH_zhu']
    Types = ['Event']
    #Types = ['NSBH_q_range'] 
    #Types = ['BNS_alsing']
    fig, ax = plt.subplots(figsize=(16, 12))
    for n, t in enumerate(Types):
        prob_events, prob_norm_events, mej_test, chi, EOS_type = run_prob(mass, lan, chi, theor = True, Type = t)
        prob_events = np.reshape(prob_events,len(prob_events)) 
        ones = np.ones(len(prob_events))
        norm = np.max(prob_events)
        cdf = np.cumsum(prob_events)/norm
        pdf = prob_events/norm

        ax.plot(plot_mass, pdf, color=colors[n], label=labels[n])

        mej_kde.append(pdf) 

    ax.plot([.03,.03],[1e-6,1e6], color = 'black', linestyle='--')
    ax.plot([.05,.05],[1e-6,1e6], color = 'black', linestyle='--')
    ax.set_yscale('log')
    ax.set_xscale('log')
    #ax.set_xlim(-9.8, -20.2)
    plt.ylim(1e-3,1.1)
    plt.xlabel('mej')
    plt.ylabel('Probability')
    plt.legend()
    plt.grid()

    
    plotname = './output/KDE_comp_edit_test.pdf'
    plt.savefig(plotname)
    plt.close()

#---------------------------------------------------------------------------------
'''
CODE TO RUN SCRIPT AND GENERATE PLOTS

The plot code for CDFs is below, PDF's are generated above
'''
#---------------------------------------------------------------------------------

if __name__ == "__main__":

    #use this to loops over all lan frac (which only affects lightcurves) so you shouldn't have to change this
    lan_list = ['-1.00', '-2.00', '-3.00', '-4.00', '-5.00', '-9.00']
    #use this if concerned with CDF/PDFs
    lan_list = [-9.00]

    #use this to loop over range of spin values for NSBH
    chi_list = [-.75, -.5, -.25, 0, .25, .5, .75]
    #only run spin 0 (which is what your original PDF was of)
    chi_list=[0]

    #leave True
    plot_list=[]
    for lan in lan_list:
        for chi in chi_list:
            cov_tf = False 
            prob_events, prob_norm_events = np.ones(100), np.ones(100)
            plot(mass, prob_events, prob_norm_events, lan, chi, coverage_factors = cov_tf)
