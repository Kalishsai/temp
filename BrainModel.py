import pandas as pd  



def BrainModelType(Modelname,Outdir):
    if Modelname == 'GHBMC AM50':
        BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\GHBMC_AM50.csv')
        Brainsolid_Parts = [1100000,1100001,1100002,1100003,1100004,1100005,1100006,1100007,1100009,1100016,1900006]
        Brainshell_Parts = [1100010,1100011]
        Brainbeam_Parts =  [1900011,1900016]
        
    elif Modelname == 'Mouse':
        BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\Mouse.csv')
        Brainsolid_Parts = [1100000,1100001,1100002,1100003,1100004,1100005,1100006,1100007,1100009,1100016,1900006]
        Brainshell_Parts = [1100010,1100011]
        Brainbeam_Parts =  [1900011,1900016]
    
    
    elif Modelname == 'THUMS AM50':
        BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\Mouse.csv')
        Brainsolid_Parts = [1100000,1100001,1100002,1100003,1100004,1100005,1100006,1100007,1100009,1100016,1900006]
        Brainshell_Parts = [1100010,1100011]
        Brainbeam_Parts =  [1900011,1900016]
    
    elif Modelname == 'USER':
        BrainElem_Volume = pd.read_csv(Outdir + '\BrainElement_Volume\Mouse.csv')
        Brainsolid_Parts = [1100000]
        Brainshell_Parts = [1100010]
        Brainbeam_Parts =  [1900011]
        
    return BrainElem_Volume,Brainsolid_Parts,Brainshell_Parts,Brainbeam_Parts;