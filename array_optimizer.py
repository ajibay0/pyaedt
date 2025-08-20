import os
import time
import numpy as np
import psutil
from scipy.optimize import minimize
from matplotlib import pyplot as plt

from ansys.aedt.core import Hfss, settings
from ansys.aedt.core.generic.settings import settings
from ansys.aedt.core.visualization.post.common import Reports


def initHFSSsetup():
  AEDT_VERSION = "2024.2"
  NUM_CORES = 4
  NG_MODE = True # No Graphics mode flag, True = no GUI 

  project_path = "aedt\\1D_Dipole_array_model_all.aedt"
  project_name = "1D_Dipole_array_model_all"
  design_name = "arrayY5"
  setup_name = "Setup1"
  settings.enable_logger = False

  # Function to kill all AEDT processes
  def kill_aedt_processes():
      aedt_process_names = ["ansysedt.exe","ansysedtsv.exe", "AnsysEMsv.exe"]  # Windows executable names
      killed = False
      for proc in psutil.process_iter(['pid', 'name']):
          try:
              proc_name = proc.info['name'].lower()
              if any(aedt_name.lower() in proc_name for aedt_name in aedt_process_names):
                  proc.kill()
                  print(f"Killed process: {proc.info['name']} (PID: {proc.info['pid']})")
                  killed = True
          except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
              continue
      if not killed:
          print("Starting AEDT processes.")
      time.sleep(2)  # Delay to ensure processes are fully terminated

  # Kill all AEDT instances
  kill_aedt_processes()


  # Check for and remove the lock file if it exists
  lock_file = project_path + ".lock"
  if os.path.exists(lock_file):
      try:
          os.remove(lock_file)
          print(f"Removed lock file: {lock_file}")
      except PermissionError:
          raise PermissionError(f"Cannot remove lock file '{lock_file}'. Close AEDT or check file permissions.")
      except Exception as e:
          raise Exception(f"Failed to remove lock file '{lock_file}': {str(e)}")


  # Open the AEDT project
  hfss = Hfss(projectname=project_path, 
              design=design_name,  
              specified_version=AEDT_VERSION, 
              non_graphical=NG_MODE,
              # new_desktop=True,
              student_version=True)

  if hfss.design_name != design_name:
    raise ValueError(f"Design '{design_name}' not found in project '{project_name}'.")
  print(f"Activated project: {project_name}, design: {design_name}")
  setup = hfss.get_setup(setup_name)

  return hfss, setup


def evalAntenna(hfss, setup, N_samples, phases_amps, err_vect=None, target_pattern=None):
  N = 5
  phases = phases_amps[0:N]
  amps = phases_amps[N:]  
  # print('Phases: ', ','.join([f'{x:0.1f}' for x in phases]))
  # print('Amps: ',','.join([f'{x:0.2f}' for x in amps]))
  for i in range(N):  
    if abs(amps[i]) < 1e-3: amps[i] = 1e-3
    hfss.odesign.SetVariableValue("Phase"+str(i), f'{phases[i]:0.3f}rad')
    hfss.odesign.SetVariableValue("Amp"+str(i), f'{amps[i]:0.3f}V')

  time1 = time.time()
  setup.analyze()
  

  variations = hfss.available_variations.nominal_values
  variations["Theta"] = ["90deg"]
  variations["Phi"] = ["All"]
  # variations["Freq"] = ["2.4GHz"]
  far_field_data = hfss.post.get_solution_data(
      "GainTotal",  # Or the expression used in your report
      hfss.nominal_adaptive,# setup_name,
      variations=variations,
      primary_sweep_variable="Phi",
      # secondary_sweep_variable="Theta",
      report_category="Far Fields",
      context="3D"  # Or the name of your infinite sphere
  )

  # phi_data_deg = far_field_data.primary_sweep_values # Phi values in degrees
  # phi_data = [float(x) for x in phi_data_deg]
  try:
    gain_data = far_field_data.data_magnitude("GainTotal")  # Gain, linear magnitude
  except:
    gain_data = np.zeros(N_samples)
  
  if err_vect is not None and target_pattern is not None:
    errval = np.linalg.norm(gain_data - target_pattern)
    err_vect.append(errval)
    print(f'Analysis took: {(time.time()-time1):0.1f}s, err={errval:0.2f}')
  return gain_data


def optimize_antenna_array(hfss, setup, target_pattern, maxiter=1000):
    if type(target_pattern) == np.ndarray:
        pass
    elif type(target_pattern) == list:
        target_pattern = np.array(target_pattern)   

    # normalize the target pattern
    target_pattern = np.abs(target_pattern) / np.max(np.abs(target_pattern))

    # optimize the amplitudes and phases of the antenna array
    array_size = 5
    af_opt_amps_v = [ 0.13804396, -0.24838753,  0.29000823, -0.25574068,  0.14721397]
    af_opt_phases_deg = [ 0.50859738 , 0.33066983,  0.17692615,  0.48328732, -0.22207866]
    amplitudes = af_opt_amps_v#np.ones(array_size)
    phases = af_opt_phases_deg#np.zeros(array_size)
    

    err_vect = []
    
    def itter_callback(x, convergence=None):        
      phases = x[0:array_size]
      amps = x[array_size:]
      print('Phases: ', ','.join([f'{x:0.1f}' for x in phases]), flush=True)
      print('Amps: ',','.join([f'{x:0.2f}' for x in amps]), flush=True)

    # Define the error function    
    Nsamples = len(target_pattern)
    error_function = lambda x: np.linalg.norm(evalAntenna(hfss, setup, Nsamples, x, err_vect, target_pattern) - target_pattern)

    # Minimize the error function
    bounds = None
    print('bounds:',bounds)
    result = minimize(error_function, 
                      x0=np.concatenate([phases, amplitudes]), 
                      options={'maxiter':maxiter,'disp':False},
                      tol=1e-2, 
                      bounds=bounds,
                      method='Nelder-Mead', 
                      callback=itter_callback)

    optimized_amplitudes = result.x[0:array_size]
    optimized_phases = result.x[array_size:]
    
    return optimized_amplitudes, optimized_phases, err_vect


if __name__ == "__main__":
  Nsamples = 37
  phivals = np.linspace(-90, 90, Nsamples) # has to match HFSS project setup (5 deg step from -90 to 90)
  target_pattern = np.where((phivals >= -45) & (phivals <= 45), 2.0, 0.0)

  hfss, setup = initHFSSsetup()
 
  optimized_amplitudes, optimized_phases, err_vect = optimize_antenna_array(hfss, setup, target_pattern, maxiter=100)
  optimized_gain = evalAntenna(hfss, setup, Nsamples, np.concatenate([optimized_phases, optimized_amplitudes]))
  ## cleanup HFSS instance:
  hfss.release_desktop()

  plt.figure()
  plt.plot(phivals, optimized_gain, label='Optimized pattern')
  plt.plot(phivals, target_pattern, label='Target pattern')
  plt.legend()
  plt.xlabel('Phi angle, deg')
  plt.ylabel('Total Gain, mag')
  plt.xlim([-90, 90])
  plt.xticks(np.arange(-90, 90+15, 15))
  plt.grid()

  plt.figure()
  plt.plot(err_vect)
  plt.title("Error vs iteration")
  plt.xlabel("Iteration")
  plt.ylabel("Error")
  plt.grid()

  plt.show()



