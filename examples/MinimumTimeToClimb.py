import numpy as np
import asset_asrl as ast
import asset_asrl.VectorFunctions as vf
import asset_asrl.OptimalControl as oc
from asset_asrl.VectorFunctions import Arguments as Args
import matplotlib.pyplot as plt
from asset_asrl.OptimalControl.MeshErrorPlots import PhaseMeshErrorPlot,sns

## Aerodynamic Tables generated in seperate script
from MinimumTimeToClimbTables import ClalphaTab,etaTab,CD0Tab,rhoTab,sosTab,ThrustTab

'''
Minumum time to climb for supersonic aircraft. 

Original problem data comes from:

A. E. Bryson, M. N. Desai, and W. C. Hoffman, Energy-State Approximation 
in Performance Optimization of Supersonic Aircraft, 
Journal of Aircraft, Vol. 6, No. 6, November-December, 1969, pp. 481-488.

Using version reformulated in SI units by ICLOS2 
http://www.ee.ic.ac.uk/ICLOCS/ExampleMinFuelClimb.html

'''

############################################################################

g0      =  9.80665 
Lstar   =  10000           
Tstar   =  250.0             
Mstar   =  19050.864         


Astar   =  Lstar/Tstar**2
Vstar   =  Lstar/Tstar
Rhostar =  Mstar/Lstar**3
Estar   =  Mstar*(Vstar**2)
Mustar  =  (Lstar**3)/(Tstar**2)
Fstar   =  Astar*Mstar
#############################################################################

mu       = 3.986012e14      /Mustar
Re       = 6378145          /Lstar
S        = 49.2386          /(Lstar**2)
vexhaust = 1600*g0           /Vstar

#############################################################################
class AirPlane(oc.ODEBase):
    
    def __init__(self):
        
        XtU = oc.ODEArguments(4,1)
        
        # Altitude,velocity,flight path angle, mass
        h,v,fpa,mass = XtU.XVec().tolist()  
        # Angle of attack
        alpha = XtU.UVar(0)
        
        
        rho = rhoTab(h*Lstar)/Rhostar  
        sos = sosTab(h*Lstar)/Vstar
        
        Mach = v/sos
        CD0 = CD0Tab(Mach)
        Clalpha = ClalphaTab(Mach)
        eta     = etaTab(Mach)
        
        Thrust = ThrustTab(Mach,h*Lstar)/Fstar
        
        CD = CD0 + eta*Clalpha*(alpha**2)
        CL = Clalpha*alpha
        q  = 0.5*rho*(v**2)
        D  = q*S*CD
        L  = q*S*CL
        r  = h + Re
        
        
        hdot   = v*vf.sin(fpa);
        vdot   = (Thrust*vf.cos(alpha)-D)/mass - mu*vf.sin(fpa)/(r**2);
        fpadot = (Thrust*vf.sin(alpha)+L)/(mass*v) +vf.cos(fpa)*( v/r - mu/(v*(r**2)));
        mdot   = -Thrust/vexhaust
        
        ode = vf.stack([hdot,vdot,fpadot,mdot])
        
        super().__init__(ode, 4, 1)
        
#############################################################################
def Plot(Traj):
    
    sns.set_context("paper")

    fig = plt.figure()
    ax0 = plt.subplot(421)
    ax1 = plt.subplot(423)
    ax2 = plt.subplot(425)
    ax3 = plt.subplot(427)
    ax4 = plt.subplot(122)

    T1 = np.array(Traj).T
    
    
    ax0.plot(T1[4]*Tstar,T1[0]*Lstar)
    ax1.plot(T1[4]*Tstar,T1[1]*Vstar)
    ax2.plot(T1[4]*Tstar,T1[2]*180/np.pi)
    ax3.plot(T1[4]*Tstar,T1[5]*180/np.pi)
    
    v=np.linspace(0,max(T1[1])*1.1,30)
    h =np.linspace(0,max(T1[0])*1.05,30)
    V,H = np.meshgrid(v,h)
    
    ## Energy height contours from bryson's paper
    def EnergyHeight(v,h):
        g= mu/(h + Re)**2
        return (.5*v**2)/g + h
    E = EnergyHeight(V,H)
    ax4.plot(T1[1]*Vstar,T1[0]*Lstar)
    cs = ax4.contour(V*Vstar,H*Lstar,E,colors= 'k',levels = 7,linestyles='dotted')
    
    ax4.scatter(T1[1][0]*Vstar,T1[0][0]*Lstar,color='k')
    ax4.scatter(T1[1][-1]*Vstar,T1[0][-1]*Lstar,color='k',marker='*')

    ax0.grid(True)
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    ax4.grid(True)

    ax0.set_ylabel(r"$h\;(m)$")
    ax1.set_ylabel(r"$v\;(\frac{m}{s})$")
    ax2.set_ylabel(r"$\gamma\;(^\circ)$")
    ax3.set_ylabel(r"$\alpha\;(^\circ)$")
    ax3.set_xlabel(r"$t\;(s)$")
    ax4.set_ylabel(r"$h\;(m)$")
    ax4.set_xlabel(r"$v\;(\frac{m}{s})$")
    
    fig.set_size_inches(10.0, 6.0)
    fig.tight_layout()
    plt.show()


#############################################################################
if __name__ == "__main__":
    
    ht0   = .010/Lstar     # Dont make exactly zero so it doesnt conflict with path constraint
    htf   = 19994.88/Lstar
    vt0   = 129.314/Vstar
    vtf   = 295.092/Vstar
    fpat0 = 0 
    fpatf = 0 
    mass0 = 19050.864/Mstar
    
    hmin     = 0
    hmax     = 21000.0/Lstar
    vmin     = 5/Vstar 
    vmax     = 600/Vstar
    fpamin   = -20*np.pi/180
    fpamax   = 40*np.pi/180
    massmin  = 16500/Mstar
    alphamin = -np.pi/4 
    alphamax = np.pi/4
    
    tfig = 200/Tstar
    
    XtU0 = np.array([ht0,vt0,fpat0,mass0,0,0])
    XtUf = np.array([htf,vtf,fpatf,mass0,tfig,0])    
    Traj = [ XtU0*(1-t) +  XtUf*t for t in np.linspace(0,1,100) ]
    
    
    ode = AirPlane()

    phase = ode.phase("LGL5",Traj,50)
    phase.setControlMode("HighestOrderSpline")
    phase.addBoundaryValue("First",range(0,5),[ht0,vt0,fpat0,mass0,0])
    
    phase.addLUVarBound("Path",0,hmin,hmax)
    phase.addLUVarBound("Path",1,vmin,vmax)
    phase.addLUVarBound("Path",2,fpamin,fpamax)
    phase.addLowerVarBound("Last",3,massmin)
    phase.addLUVarBound("Path",5,alphamin,alphamax)
    phase.addBoundaryValue("Last",range(0,3),[htf,vtf,fpatf])
    phase.addDeltaTimeObjective(1.0)
    
    phase.setAdaptiveMesh(True)
    phase.optimizer.PrintLevel=1
    phase.setThreads(8,8)
    phase.setMeshTol(1.0e-7)
    phase.optimize()
    
    Traj = phase.returnTraj()
    Tab = phase.returnTrajTable()
    
    print("Minimum Time to Climb:{0:.2f}s".format(Traj[-1][4]*Tstar))
    
    PhaseMeshErrorPlot(phase,False)
    Plot(Traj)
    
    
    
    
    
    

    
    
    
    
    
        
    
    

    
    
    
    
    

        
        
        
        
        
        
        
        