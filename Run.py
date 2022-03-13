import StrainUAPI
import time


start_time = time.time()

WorkDir = 'H:\Demo\WorkingDirectory'  # Specify the Working Directory in your computer 

Modeltype = 'GHBMC AM50'
# Specify brain model model type
# GHBMC MALE 50 -> Modeltype = 'GHBMC AM50'
# MOUSE         -> Modeltype = 'MOUSE'
# THUMS MALE 50 -> Modeltype = 'THUMS AM50'
# USER DEFINED  -> Modeltype = 'USER'

FileType = 'SAME'
# Specify the filetype of simulation files in working directory 
# FileType = 'SAME' -> If all simulation files in the working directory are based on same model data 
# FileType = 'DIFFERENT' -> If all simulation files in the working directory are based on different model data 
 
StrainUAPI.Execute(WorkDir,Modeltype,FileType) #Runs functions in StrainAPI


print("COMPUTATION TIME--- %s seconds ---" % (time.time() - start_time))  