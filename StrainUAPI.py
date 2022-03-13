# Importing LS-PREPOST API Libraries
from LsPrePost import execute_command, echo
from LsPrePost import check_if_part_is_active_u as check_u
from LsPrePost import cmd_result_get_value_count as crgvc
from LsPrePost import cmd_result_get_value as crgv
import DataCenter as dc
from DataCenter import Type, Ipt
import LsPrePost as lspp

# Importing python libraries
import pandas as pd             # Library needed to installed 
import numpy as np              # Library needed to installed
import time
import os
import math

import BrainModel

# Creating dataframe for outputs
CSDM_Results = pd.DataFrame()
DTMeanMPS_Results = pd.DataFrame()
MPS_Results = pd.DataFrame()

# Global varibles for loop iteration
iterator1 = iterator2 = 0

# Display all parts in the GUI 
def Show_allparts():
    execute_command('selectpart beam on')
    execute_command('selectpart shell on')
    execute_command('selectpart tshell on')
    execute_command('selectpart solid on')
    execute_command('selectpart SBelt on')
    execute_command('selectpart CNRB on')
    execute_command('selectpart all on')

# Display solid parts in the GUI    
def Show_solidparts():
    execute_command('selectpart beam off')
    execute_command('selectpart shell off')
    execute_command('selectpart tshell off')
    execute_command('selectpart SBelt off')
    execute_command('selectpart CNRB off')

# Display shell parts in the GUI
def Show_shellparts():
    execute_command('selectpart beam off')
    execute_command('selectpart solid off')
    execute_command('selectpart tshell off')
    execute_command('selectpart SBelt off')
    execute_command('selectpart CNRB off')

# Display shell parts in the GUI
def Show_beamparts():
    execute_command('selectpart shell off')
    execute_command('selectpart solid off')
    execute_command('selectpart tshell off')
    execute_command('selectpart SBelt off')
    execute_command('selectpart CNRB off')
    
# Clear the output dataframe and global variables
def FlushGlobal():
    global CSDM_Results,MPS_Results,DTMeanMPS_Results
    global iterator1,iterator2
    
    CSDM_Results = pd.DataFrame()
    DTMeanMPS_Results = pd.DataFrame()
    MPS_Results = pd.DataFrame()
    
    iterator1 = 0 
    iterator2 = 0    


# def BrainModelType(Modelname,Outdir):
    # if Modelname == 'GHBMC AM50':
        # BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\GHBMC_AM50.csv')
        # Brainsolid_Parts = [1100000,1100001,1100002,1100003,1100004,1100005,1100006,1100007,1100009,1100016,1900006]
        # Brainshell_Parts = [1100010,1100011]
        # Brainbeam_Parts =  [1900011,1900016]
    # elif Modelname == Mouse:
        # BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\Mouse.csv')
    # return BrainElem_Volume,Brainsolid_Parts,Brainshell_Parts,Brainbeam_Parts;

# Get model information from the keyword file    
def Modelinfo(Keypath,FOutpath):
    
    execute_command(Keypath)
    Show_allparts()
    
    execute_command('partsort sort')
    for i in range (0,28):
        execute_command('partsort fieldset '+str(i)+' 0')
    execute_command('partsort fieldset 0 1')                # Element Type 
    execute_command('partsort fieldset 1 1')                # Part ID
    execute_command('partsort fieldset 3 1')                # Part Name
    execute_command('partsort fieldset 4 1')                # Section ID
    execute_command('partsort fieldset 6 1')                # Material ID
    execute_command('partsort fieldset 8 1')                # Material Name 
    execute_command('partsort fieldset 12 1')               # Thickness
    execute_command('partsort fieldset 14 1')               # Mass
    execute_command('partsort fieldset 18 1')               # Number of Elements in parts
    
    execute_command('partsort write "'+FOutpath+'\KeywordModelinfo.csv"')
    Modelinfo = pd.read_csv(FOutpath+'\KeywordModelinfo.csv')
    execute_command('partsort done')
    return Modelinfo

# Get MPS strain of all solid elements from all selected parts,MPS and CSDM values of brain
def MPS_SolidElements(Solid_Parts,Elem_Volume,FileOutpath):
    
    Show_allparts()
    Show_solidparts()
    
    D3plot_states = dc.get_data('num_states')
    Num_solidelements = dc.get_data('num_solid_elements')
    Allsolid_ElementIDs = dc.get_data('element_ids',type=Type.SOLID)
    
    MPS_allsolid = pd.DataFrame()
    
    for s in range(D3plot_states):
        Strain = dc.get_data('strain_maxprincipal',type=Type.SOLID, ipt=Ipt.MEAN, ist=s+1) 
        MPS_allsolid[str(s)] = Strain 
    MPS_allsolid['Max MPS'] = MPS_allsolid.max(axis=1)  
    MPS_allsolid.insert(loc=0,column ="Element ID",value = Allsolid_ElementIDs)
    MaxMPS_allsolid = MPS_allsolid['Max MPS'].to_numpy() 
 
    Selelement_ids =[]
    for p in range (len(Solid_Parts)):
        Selelement_ids.extend(dc.get_data('elemofpart_ids',type=Type.SOLID,id = Solid_Parts[p]))
        
    SelBrainMPS = MPS_allsolid[MPS_allsolid['Element ID'].isin(Selelement_ids)==True]
    os.makedirs(FileOutpath +'\SolidParts', exist_ok=True)
    os.makedirs(FileOutpath +'\SolidParts\TimeseriesData', exist_ok=True)
    SelBrainMPS.to_csv(FileOutpath +'\SolidParts\TimeseriesData\AllElement-MPS[Selected Parts].csv')

    if Elem_Volume.shape[0]!=0:
        Volelement_ids = Elem_Volume['Element ID'].tolist()
        BrainMPS = MPS_allsolid[MPS_allsolid['Element ID'].isin(Volelement_ids)==True]
        BrainMPS.to_csv(FileOutpath +'\SolidParts\TimeseriesData\AllElement-MPS[Brain Parts].csv')
        MaxMPS_brain = BrainMPS['Max MPS'].to_numpy()
        Calculate_MPSResults(MaxMPS_brain,'Whole Brain',1)
        if BrainMPS.shape[0] == len(Volelement_ids):
            Calculate_CSDMResults(MaxMPS_brain,Volelement_ids,'Whole Brain',1,Elem_Volume)

    Show_allparts()
    return MPS_allsolid 

# Get MPS strain of all solid elements from each parts,MPS and CSDM values of brain parts    
def MPS_PartwiseSolid(MPS_allsolid,ModelInfo,Solid_Parts,Elem_Volume,FileOutpath):
    
    Show_allparts()
    Show_solidparts()

    global iterator1, iterator2 

    #Get all valid partIDs
    Partids = dc.get_data('validpart_ids')

    Activepardids = []
    for p in range(len(Partids)):        
        if Partids[p] in Solid_Parts:
        
            Eleminpart = dc.get_data('elemofpart_ids',type=Type.SOLID,id = Partids[p]) 
            PartwiseMPS = MPS_allsolid[MPS_allsolid['Element ID'].isin(Eleminpart)==True]  
            PartwiseMPSMax = PartwiseMPS['Max MPS'].to_numpy()
            CurrentPartName = ModelInfo.loc[ModelInfo['PartId'] == Partids[p], 'PartName'].iloc[0]  
            
            Activepardids.append(Partids[p]) 
            iterator1 +=1
         
            Calculate_MPSResults(PartwiseMPSMax,CurrentPartName,Partids[p])
            Calculate_TimeseriesMPSmean(PartwiseMPS,CurrentPartName)
            os.makedirs(FileOutpath +'\SolidParts\PartwiseMPS', exist_ok=True)
            buf = FileOutpath +'\SolidParts\PartwiseMPS\MPS_SOLID-PartID_'+str(Partids[p])+"_["+ CurrentPartName+"].csv"
            PartwiseMPS.to_csv(buf)
                
            BrainMPS = Elem_Volume[Elem_Volume['Element ID'].isin(Eleminpart)==True]
            if BrainMPS.shape[0] == len(Eleminpart):
                iterator2 +=1
                Calculate_CSDMResults(PartwiseMPSMax,Eleminpart,CurrentPartName,Partids[p],Elem_Volume)
               
    Updated_DTMeanMPS = DTMeanMPS_Results.T
    Updated_DTMeanMPS.insert(loc=0,column ="Part ID",value = Activepardids)
    Updated_DTMeanMPS.to_csv(FileOutpath +'\SolidParts\TimeseriesData\Mean-DTMPS[SelectedParts].csv')
    CSDM_Results.to_csv(FileOutpath +'\SolidParts\CSDM-Result[Brainparts].csv')
    MPS_Results.to_csv(FileOutpath +'\SolidParts\MPS-Result[SelectedParts].csv')

    FlushGlobal()        
    Show_allparts()
    
# Get MPS strain of all solid elements from all selected parts and MPS values of all selected parts
def MPS_ShellElements(Shell_Parts,FileOutpath):
    Show_allparts()
    Show_shellparts()
    
    D3plot_states = dc.get_data('num_states')
    Num_shellelements = dc.get_data('num_shell_elements')
    Allshell_ElementIDs = dc.get_data('element_ids',type=Type.SHELL)
    
    MPS_allshell = pd.DataFrame()
    
    for s in range(D3plot_states):
        Strain = dc.get_data('strain_maxprincipal',type=Type.SHELL, ipt=Ipt.MEAN, ist=s+1) 
        MPS_allshell[str(s)] = Strain 
    MPS_allshell['Max MPS'] = MPS_allshell.max(axis=1)  
    MPS_allshell.insert(loc=0,column ="Element ID",value = Allshell_ElementIDs)

    Selelement_ids =[]
    for p in range (len(Shell_Parts)):
        Selelement_ids.extend(dc.get_data('elemofpart_ids',type=Type.SHELL,id = Shell_Parts[p]))
        
    SelBrainMPS = MPS_allshell[MPS_allshell['Element ID'].isin(Selelement_ids)==True]
    os.makedirs(FileOutpath +'\ShellParts\TimeseriesData', exist_ok=True)
    SelBrainMPS.to_csv(FileOutpath +'\ShellParts\TimeseriesData\AllElement-MPS[Selected Parts].csv')

    MaxMPS_brain = SelBrainMPS['Max MPS'].to_numpy()
    Calculate_MPSResults(MaxMPS_brain,'All Selected Shell',1)
    
     
    Show_allparts()
    return MPS_allshell

# Get MPS strain of all solid elements from each parts and MPS values of selected parts 
def MPS_PartwiseShell(MPS_allshell,ModelInfo,Shell_Parts,FileOutpath):
    Show_allparts()
    Show_shellparts()

    global iterator1, iterator2 
    Partids = dc.get_data('validpart_ids')

    Activepardids = []
    for p in range(len(Partids)):                                                                    
        if Partids[p] in Shell_Parts:
        
            Eleminpart = dc.get_data('elemofpart_ids',type=Type.SHELL,id = Partids[p])              
            PartwiseMPS = MPS_allshell[MPS_allshell['Element ID'].isin(Eleminpart)==True]           
            PartwiseMPSMax = PartwiseMPS['Max MPS'].to_numpy()
            CurrentPartName = ModelInfo.loc[ModelInfo['PartId'] == Partids[p], 'PartName'].iloc[0]  
                
            Activepardids.append(Partids[p]) 
            iterator1 +=1
               
            Calculate_MPSResults(PartwiseMPSMax,CurrentPartName,Partids[p])
                
            Calculate_TimeseriesMPSmean(PartwiseMPS,CurrentPartName)
            os.makedirs(FileOutpath +'\ShellParts\PartwiseMPS', exist_ok=True)
            buf = FileOutpath +'\ShellParts\PartwiseMPS\MPS_SHELL-PartID_'+str(Partids[p])+"_["+ CurrentPartName+"].csv"
            PartwiseMPS.to_csv(buf)
               
    Updated_DTMeanMPS = DTMeanMPS_Results.T
    Updated_DTMeanMPS.insert(loc=0,column ="Part ID",value = Activepardids)
    Updated_DTMeanMPS.to_csv(FileOutpath +'\ShellParts\TimeseriesData\Mean-DTMPS[SelectedParts].csv')
    MPS_Results.to_csv(FileOutpath +'\ShellParts\MPS-Result[SelectedParts].csv')

    FlushGlobal()        
    Show_allparts()

# Get Axial strain of all beam elements from each parts and Max axial strain value of all selected parts 
def Astrain_BeamElement(Beam_Parts,FileOutpath):
    Show_allparts()
    Show_beamparts() 
    
    D3plot_states = dc.get_data('num_states')
    Num_beamelements = dc.get_data('num_beam_elements')
    Allbeam_ElementIDs = dc.get_data('element_ids',type=Type.BEAM)
    
    Axialstrain_allbeam = pd.DataFrame()
    
    for s in range(D3plot_states):
        AStrain = dc.get_data('axial_strain',type=Type.BEAM, ipt=Ipt.MEAN, ist=s+1) 
        Axialstrain_allbeam[str(s)] = AStrain 
    Axialstrain_allbeam['Max Axialstrain'] = Axialstrain_allbeam.max(axis=1)  #Calculate Max MPS for each elements
    Axialstrain_allbeam.insert(loc=0,column ="Element ID",value = Allbeam_ElementIDs)

    Selelement_ids =[]
    for p in range (len(Beam_Parts)):
        Selelement_ids.extend(dc.get_data('elemofpart_ids',type=Type.BEAM,id = Beam_Parts[p]))
        
    SelAxialstrain = Axialstrain_allbeam[Axialstrain_allbeam['Element ID'].isin(Selelement_ids)==True]
    os.makedirs(FileOutpath +'\BeamParts\TimeseriesData', exist_ok=True)
    SelAxialstrain.to_csv(FileOutpath +'\BeamParts\TimeseriesData\AllElement-MPS[Selected Parts].csv')

    MaxAxial_strain = SelAxialstrain['Max Axialstrain'].to_numpy()
    Calculate_AstrianResults(MaxAxial_strain,'All Selected Beams',1)
    

    Show_allparts()
    return Axialstrain_allbeam   

# Get Axial strain strain of all solid elements from each parts and Max Axial strain values of selected parts 
def Astrain_PartwiseBeam(MaxAxial_strain,ModelInfo,Beam_Parts,FileOutpath):
    Show_allparts()
    Show_beamparts()

    global iterator1, iterator2 

    Partids = dc.get_data('validpart_ids')

    Activepardids = []
    for p in range(len(Partids)):
        if Partids[p] in Beam_Parts:
    
            Eleminpart = dc.get_data('elemofpart_ids',type=Type.BEAM,id = Partids[p])              
            PartwiseAxialstrain = MaxAxial_strain[MaxAxial_strain['Element ID'].isin(Eleminpart)==True]           
            PartwiseAXMax = PartwiseAxialstrain['Max Axialstrain'].to_numpy()
            CurrentPartName = ModelInfo.loc[ModelInfo['PartId'] == Partids[p], 'PartName'].iloc[0] 
        
            Activepardids.append(Partids[p]) 
            iterator1 +=1
                
            Calculate_AstrianResults(PartwiseAXMax,CurrentPartName,Partids[p])
                
            Calculate_TimeseriesAstrianmean(PartwiseAxialstrain,CurrentPartName)
            os.makedirs(FileOutpath +'\BeamParts\Partwise_Axialstrain', exist_ok=True)
            buf = FileOutpath +'\BeamParts\Partwise_Axialstrain\AxialStrain_BEAM-PartID_'+str(Partids[p])+"_["+ CurrentPartName+"].csv"
            PartwiseAxialstrain.to_csv(buf)
               
    Updated_DTMeanAstrain = DTMeanMPS_Results.T
    Updated_DTMeanAstrain.insert(loc=0,column ="Part ID",value = Activepardids)
    Updated_DTMeanAstrain.to_csv(FileOutpath +'\BeamParts\TimeseriesData\Mean-DTAxialStrain[SelectedParts].csv')
    MPS_Results.to_csv(FileOutpath +'\BeamParts\AxialStrain-Result[SelectedParts].csv')

    FlushGlobal()        
    Show_allparts()   
    
# Get Astrainmax,mean and Astrain95 for all beam parts    
def Calculate_AstrianResults(AstrainMax,CurrentPartName,Current_PartID):

    MPS_Results.at[iterator1, 'Part_ID'] = Current_PartID
    MPS_Results.at[iterator1, 'PartName'] = CurrentPartName
    MPS_Results.at[iterator1, 'Max_AxialStrain'] = np.max(AstrainMax)
    MPS_Results.at[iterator1, 'Mean_AxialStrain'] = np.mean(AstrainMax)
    MPS_Results.at[iterator1, 'AxialStrain95'] = np.percentile(AstrainMax,95)
    
# Get Timeseries Axial strain of all selected parts
def Calculate_TimeseriesAstrianmean(PartwiseAstrain,CurrentPartName):
    PartwiseAstrain = PartwiseAstrain.drop("Element ID",axis =1)
    PartwiseAstrain = PartwiseAstrain.iloc[: , :-1]
    Mean_Astrain =PartwiseAstrain.mean(axis=0).values
    DTMeanMPS_Results[CurrentPartName] = Mean_Astrain.tolist()  

# Get MPSmax,MPS mean and MPS95 for whole brain and selected brain    
def Calculate_MPSResults(MPSMax,CurrentPartName,Current_PartID):

    MPS_Results.at[iterator1, 'Part_ID'] = Current_PartID
    MPS_Results.at[iterator1, 'PartName'] = CurrentPartName
    MPS_Results.at[iterator1, 'Max_MPS'] = np.max(MPSMax)
    MPS_Results.at[iterator1, 'Mean_MPS'] = np.mean(MPSMax)
    MPS_Results.at[iterator1, 'MPS95'] = np.percentile(MPSMax,95)
    
# Get Timeseries MeanMPS of all selected parts
def Calculate_TimeseriesMPSmean(PartMPS,CurrentPartName):
    PartMPS = PartMPS.drop("Element ID",axis =1)
    PartMPS = PartMPS.iloc[: , :-1]
    Mean_MPS =PartMPS.mean(axis=0).values
    DTMeanMPS_Results[CurrentPartName] = Mean_MPS.tolist()
    
# Get CSDM results of all brain parts  
def Calculate_CSDMResults(Elementinpart_MPS,ElementIDs,CurrentPartName,Current_PartID,BrainElem_Volume):
 
    CSDM_Matrix = pd.DataFrame()
    CSDM_Matrix["ElementID"] = ElementIDs
    CSDM_Matrix["strain"] = Elementinpart_MPS
    
    CSDM_Matrix['strain%'] = [i -math.floor(i) for i in Elementinpart_MPS]
    Percentile = [5,10,15,20,25]

    CSDM_Results.at[iterator2, 'Part_ID'] = Current_PartID
    CSDM_Results.at[iterator2, 'PartName'] = CurrentPartName

    for p in range(len(Percentile)):
        CSDM_Results.at[iterator2, 'CSDM'+str(Percentile[p])] = CSDM_Percentile(CSDM_Matrix,Percentile[p],BrainElem_Volume)
        
# Get CSDM5,10,15,20,25 results of all brain parts 
def CSDM_Percentile(ElemStrain_Matrix,Percentile,BrainElem_Volume):

    Elementsinpart = []
    for i in range(ElemStrain_Matrix.shape[0]):
        if ElemStrain_Matrix.loc[i,'strain%']>=Percentile/100:
            Elementsinpart.append(ElemStrain_Matrix.loc[i,'ElementID'])

    StrainVolume = BrainElem_Volume[BrainElem_Volume['Element ID'].isin(Elementsinpart)==True]
    StrainVolume = StrainVolume.iloc[:,1].sum()
    Volume = BrainElem_Volume[BrainElem_Volume['Element ID'].isin(ElemStrain_Matrix['ElementID'].tolist())==True]
    Volume = Volume.iloc[:,1].sum()
    return StrainVolume/Volume



# Run all strain estimation API functions 
def Execute(WorkDir,Modeltype,FileType):
    os.chdir(WorkDir)
    currentdir = os.getcwd()
    Files = os.listdir(currentdir)
    Outdir = currentdir.replace('WorkingDirectory','')
    os.makedirs(Outdir +'\DataOutput', exist_ok=True)

    Volume,Solidparts,Shellparts,BeamParts = BrainModel.BrainModelType(Modeltype,Outdir)


    if FileType == 'DIFFERENT':

        ModelIF = []
        for f in range(len(Files)):
            Path = str(currentdir) + "\\"+ str(Files[f])
            listfile = os.listdir(Path)
            Keyfile = [i for i in listfile if i[-2:]== '.k' or i[-4:]== '.key' ]
            Keypath = 'open keyword "'+Path +'\\'+str(Keyfile[0])
    
            FOutpath = Outdir +'\DataOutput\\'+str(Files[f])
            os.makedirs(FOutpath, exist_ok=True)
    
            Case = Modelinfo(Keypath,FOutpath)
            ModelIF.append(Case)
    
        for f in range(len(Files)):
            Path = str(currentdir) + "\\"+ str(Files[f])
            D3path = 'open d3plot "'+Path +'\d3plot"'
    
            FOutpath = Outdir +'\DataOutput\\'+str(Files[f])
    
            execute_command(D3path)
    
            if len(Solidparts)!=0:
                MPS_PartwiseSolid(MPS_SolidElements(Solidparts,Volume,FOutpath),ModelIF[f],Solidparts,Volume,FOutpath)
            else:
                print("No solid parts selected ")
        
            if len(Shellparts)!=0:
                MPS_PartwiseShell(MPS_ShellElements(Shellparts,FOutpath),ModelIF[f],Shellparts,FOutpath)

            else:
                print("No shell parts selected ")
        
            if len(BeamParts)!=0:
                Astrain_PartwiseBeam(Astrain_BeamElement(BeamParts,FOutpath),ModelIF[f],BeamParts,FOutpath)

            else:
                print("No beam parts selected ")
   
        #execute_command('exit')

    elif FileType == 'SAME':

        Path = str(currentdir) + "\\"+ str(Files[0])
        listfile = os.listdir(Path)
        Keyfile = [i for i in listfile if i[-2:]== '.k' or i[-4:]== '.key' ]
        Keypath = 'open keyword "'+Path +'\\'+str(Keyfile[0])
    
        ModelIFpath = Outdir +'\DataOutput'
    
        ModelIF = Modelinfo(Keypath,ModelIFpath)


        for f in range(len(Files)):

            FOutpath = Outdir +'\DataOutput\\'+str(Files[f])
            os.makedirs(FOutpath, exist_ok=True)

            Path = str(currentdir) + "\\"+ str(Files[f])
            D3path = 'open d3plot "'+Path +'\d3plot"'

            execute_command(D3path)
    
            if len(Solidparts)!=0:
                MPS_PartwiseSolid(MPS_SolidElements(Solidparts,Volume,FOutpath),ModelIF,Solidparts,Volume,FOutpath)
            else:
                print("No solid parts selected ")
        
            if len(Shellparts)!=0:
                MPS_PartwiseShell(MPS_ShellElements(Shellparts,FOutpath),ModelIF,Shellparts,FOutpath)

            else:
                print("No shell parts selected ")
        
            if len(BeamParts)!=0:
                Astrain_PartwiseBeam(Astrain_BeamElement(BeamParts,FOutpath),ModelIF,BeamParts,FOutpath)

            else:
                print("No beam parts selected ")