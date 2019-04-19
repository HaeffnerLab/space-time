from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import lmfit
import scipy.constants as scc

class pi_time_fitter():

    def guess_tpi(self, t, exci):
        '''
        Start from the beginning of the flop.
        Use the starting guess as the first time
        the flop value goes down AND the flop has
        exceeded 0.9 excitation probability.
        '''

        last = 0
        for i, ex in enumerate(exci):
            if ex < last and last >= 0.9: return t[i-1]
            last = ex
        raise Exception('No valid pi time guess')

    def fit(self, t, exci):
        t0 = self.guess_tpi(t, exci)
        model = lambda x, tpi: np.sin(np.pi/2/tpi*np.array(x))**2
        t_pi, c = curve_fit(model, t, exci, p0 = t0)
        return t_pi[0]

class peak_fitter():
    
    def guess(self, f, p, force_guess = False):
        '''
        just take the point at the peak value
        '''
        max_index = np.where(p == p.max())[0][0]
        fmax = f[max_index]
        if (p.max() <= 0.1 and not force_guess):
            raise Exception("Peak not found")
        else:
            # center, amplitude, width guesses
            return np.array([ fmax,  p.max(), 6e-3 ])
    
    def fit(self, f, p, return_all_params = False):
        model = lambda x, c0, a, w: a*np.exp(-(x - c0)**2/w**2)
        force_guess = False
        if return_all_params: force_guess = True
        guess = self.guess(f, p, force_guess)
        popt, copt = curve_fit(model, f, p, p0=guess)
        if return_all_params:
            return popt[0], popt[1], popt[2] # center value, amplitude, width
        else:
            return popt[0] # return only the center value

class sin_fitter():
    
    def guess(self, phi, p, force_guess=False):
        '''
        just take the point at the peak value
        '''
        return np.array([max(p)-min(p),  0, 0])
    
    def fit(self, phi, p):
        model = lambda phi, amplitude, phi0, offset: -amplitude/2.0*np.cos(np.pi/180*(phi - phi0)) + 0.5 + offset
        force_guess = True
        guess = self.guess(phi, p, force_guess)
        perr = np.maximum(np.sqrt(np.array(p)*(1.0-np.array(p))/100), 1.0/(100+2)) # takes quantum projection noise as the source of uncertainty in p. ASSUMES 100 MEASUREMENT REPETITIONS
        popt, copt = curve_fit(model, phi, p, p0=guess, sigma=perr, absolute_sigma=True)
        return popt[0], popt[1]

class double_sin_fitter():
    def guess(self, phi, p, force_guess=False):
        '''
        just take the point at the peak value
        '''
        return np.array([max(p)-min(p),  0, 0])  
    
    def fit(self, phi, p):
        model = lambda phi, amplitude, phi0, offset: -amplitude/2.0*np.cos(2*np.pi/180*(phi - phi0)) + 0.5 + offset
        force_guess = True
        guess = self.guess(phi, p, force_guess)
        perr = np.maximum(np.sqrt(np.array(p)*(1.0-np.array(p))/100), 1.0/(100+2)) # takes quantum projection noise as the source of uncertainty in p. ASSUMES 100 MEASUREMENT REPETITIONS
        popt, copt = curve_fit(model, phi, p, p0=guess, sigma=perr, absolute_sigma=True)
        return popt[0], popt[1]  


class rot_ramsey_fitter():  
    def fit(self, f, p):
        guess = [60,10,5,0.8,100]
        popt, copt = curve_fit(self.rot_ramsey_decay, f, p, p0=guess)
        return 2*popt[0], popt[1] #contrast and phase

    def rot_ramsey_decay(self, times_us, sigma_l, Omega_kHz, delta_kHz, f_trap_MHz, f_rot_kHz):
        # convert inputs to SI
        times = 1e-6 * times_us
        Omega = 1e3 * 2*np.pi * Omega_kHz
        delta = 1e3 * 2*np.pi * delta_kHz
        w_trap = 1e6 * 2*np.pi * f_trap_MHz
        w_rot = 1e3 * 2*np.pi * f_rot_kHz
        #fix parameters for diffusion measurment
        scale = 1
        Delta_l = 1
        # calculate moment of inertia
        m = 40*scc.atomic_mass
        r = 1/2.0 * (scc.e**2/(4*np.pi*scc.epsilon_0) * 2.0/(m*(w_trap**2 - w_rot**2)))**(1/3.0) #rotor radius
        I = 2*m*r**2  # moment of inertia

        # calculate l distribution and detunings
        l_0 = I*w_rot/scc.hbar
        ls = np.arange(int(l_0-3*sigma_l), int(l_0+3*sigma_l))
        c_ls_unnorm = np.exp(-(ls-l_0)**2/(4.0*sigma_l**2))
        c_ls = c_ls_unnorm/np.linalg.norm(c_ls_unnorm)
        delta_ls = scc.hbar*Delta_l/I*(l_0-ls) + delta

        def calc_ramsey_exc(c_ls, delta_ls, Omega, T):
            Omega_gens = np.sqrt(Omega**2 + delta_ls**2) #generalized Rabi frequency
            u1s = np.pi*Omega_gens/(4*Omega)
            u2s = delta_ls*T/2.0
            return sum(np.abs(c_ls)**2 * (2*Omega/Omega_gens**2*np.sin(u1s) * (Omega_gens*np.cos(u1s)*np.cos(u2s) - delta_ls*np.sin(u1s)*np.sin(u2s)))**2)
            

        return [scale * calc_ramsey_exc(c_ls, delta_ls, Omega, T) for T in times]

def print_result(result):

    for k in result.var_names:
       print(k + " = " + str(result.params[k].value))

class scat_rate_fitter():
 
    def fcn2min(self, params, x, data, return_fit = False):
        """ model decaying sine wave, subtract data"""
        A = params['A'].value
        alpha = params['alpha'].value
        delta = params['delta'].value
    
        self.gamma = 21.87
        #model = A*2*alpha*(x/gamma**2)/(1+(2*alpha*x/gamma**2)+4*(delta/gamma)**2)
        model = A * alpha/(1 + alpha + 4*(x - delta)**2/self.gamma**2)

        if return_fit:
            return model
        else:
            return model - data
   
    def guess(self, counts):
        return 424.0, 0.2, max(counts)
    
    def fit(self, freq, counts, spec_time = 400.0): 
        guess = self.guess(counts)

        A_calib = 8.5/400.0

        # create a set of Parameters
        params = lmfit.Parameters()
        params.add('delta', value = guess[0], min = 400.0, max = 560.0, vary = True)
        params.add('alpha', value = guess[1], min = 0.1, max = 10.0, vary = True)
        params.add('A', value = spec_time * A_calib, vary = False)

        x = freq
        y = counts
        minner = lmfit.Minimizer(self.fcn2min, params, fcn_args=(x, y))
        result = minner.minimize()

        alpha_fit = result.params['alpha'].value
        delta_fit = result.params['delta'].value
        A_fit = result.params['A'].value

        print alpha_fit
        print delta_fit
        print A_fit

        rabi_freq = np.sqrt(alpha_fit * self.gamma**2 / 2.0) #in MHz



        plt.plot(freq, self.fcn2min(result.params, freq, None, return_fit = True))
        plt.plot(freq, counts, 'ko')
        xpos = .1*(max(x)-min(x)) + min(x)
        ypos = .8*(max(y)-min(y)) + min(y)
        plt.annotate('Rabi Frequency \n in MHz = ' + str(rabi_freq), xy = (xpos, ypos), xytext = (xpos, ypos))
        plt.xlabel('Real Frequency (MHz)')
        plt.ylabel('kCounts')
        plt.show()

        return rabi_freq

class old_old_scat_rate_fitter():
 
    def fcn2min(self, params, x, data, return_fit = False):
        """ model decaying sine wave, subtract data"""
        A = params['A'].value
        alpha = params['alpha'].value
        delta = params['delta'].value
    
        gamma = 2*np.pi*21.87e6
        model = A*2*alpha*(x/gamma**2)/(1+(2*alpha*x/gamma**2)+4*(delta/gamma)**2)

        if return_fit:
            return model
        else:
            return model - data
   
    def guess(self,counts):
        return 2*np.pi*22.0e6, 5.0e20, max(counts)
    
    def fit(self, PAO_log, counts):        
        PAO = 1.0e-3*10.0**(PAO_log/10.0)#b/c AOM power is in dBm

        guess = self.guess(counts)

        # create a set of Parameters
        params = lmfit.Parameters()
        params.add('delta', value = guess[0], min = 2*np.pi*10.0e6, max = 2*np.pi*100e6, vary = True)
        params.add('alpha', value = guess[1], min = 1e19, max = 1e21, vary = True)
        params.add('A', value = guess[2], min = 70.0, vary = True)

        x = PAO
        y = counts
        minner = lmfit.Minimizer(self.fcn2min, params, fcn_args=(x, y))
        result = minner.minimize()

        alpha_fit = result.params['alpha'].value
        delta_fit = result.params['delta'].value
        A_fit = result.params['A'].value

        print alpha_fit
        print delta_fit/2/np.pi/1e6
        print A_fit

        plt.plot(PAO_log, self.fcn2min(result.params, PAO, None, return_fit = True))
        plt.plot(PAO_log, counts, 'ko')
        plt.show()

        return alpha_fit

class old_scat_rate_fitter():
    
    def guess(self,counts):
        return 2*np.pi*20.0e6, 1.0e20, max(counts)
    
    def fit(self, PAO_log, counts):
        PAO = 1.0e-3*10.0**(PAO_log/10.0)#b/c AOM power is in dBm
        gamma = 2*np.pi*21.87e6
        model = lambda x, delta, alpha, A: A*2*alpha*(x/gamma**2)/(1+(2*alpha*x/gamma**2)+4*(delta/gamma)**2) #(rabi_freq**2 = alpha * power to the aom (PAO))
        guess = self.guess(counts)
        popt, copt = curve_fit(model, PAO, counts, p0=guess)
        delta_fit = popt[0]
        alpha_fit = popt[1]
        A_fit = popt[2]
        print delta_fit, alpha_fit, A_fit
                
        plt.plot(PAO_log, model(PAO,delta_fit,alpha_fit,A_fit))
        plt.plot(PAO_log, counts,'ko')
        plt.show()
        
        return alpha_fit 
        

        
