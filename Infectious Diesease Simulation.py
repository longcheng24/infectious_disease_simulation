#An object-oriented discrete event simulator
#Using it to experiment with the spread of infectious diseases

from random import random, randint, sample, choice
import matplotlib.pyplot as plt
from ast import literal_eval

'''Roll a weighted die. Returns True with probability p.'''
def rolldie (p):
    return(random() <= p)

class Disease():
    def __init__(self, name='influenza', t=0.95, E=2, I=7, r=0.0, Q=0): 
        self.name=name
        self.t=t   # Transmissivity: how easy is it to pass on?      
        self.E=E   # Length of exposure (in days)
        self.I=I   # Length of infection (in days)  
        self.r=r   # Probability of lifelong immunity at recovery 
        self.Q=0   # period of quarantine

    def quarantine(self ,Q=0):
        if Q>=self.I:
            self.Q=I
        else:
            self.Q = Q

class Agent():
    def __init__(self,typ,s,q):
        self.typ=typ        #Agent type 
        self.s=s            #Agent's susceptibility value
        self.q=q            #Quarantine compliance probability
        self.disease = []   #Disease list for each agent
        self.c = {}         #counter dictionary
        self.v = {}         #vaccination state dictionary
        self.qDay={}        #quarantine time for each disease
        self.qFlag = False  #aFlag returns whether agent has been quarantined

    def state(self,disease):
        return(bool(self.c.get(disease)))

    def vaccinate(self,v,disease,coverage):
        if rolldie(coverage):
            self.v[disease] = v
                  
    def infect(self,other,disease):
        if(self.v.get(disease)):
            v=self.v.get(disease)
        else:
            v=1
        if other.c.get(disease)>0 and not self.state(disease) and rolldie(self.s*v*disease.t) and not self.qFlag and not other.qFlag:
            self.c[disease] = disease.E + disease.I + 1
            self.disease.append(disease) 
            return(True)
        return(False)
    
    '''Update the status of the agent.'''
    def update(self,disease):
        if self.c.get(disease) == disease.I and rolldie(self.q): 
            disease.quarantine()
            if disease.Q > 0:
                self.qDay[disease]=disease.Q
                self.qFlag = True
            else:
                self.qFlag = False
        if self.c.get(disease) == disease.I-disease.Q: 
            if self.qDay.get(disease):
                del self.qDay[disease]
                if not bool(self.qDay):
                    self.qFlag = True
                else:
                    self.qFlag = False
        if self.qDay.get(disease) and self.qDay.get(disease) > 1:
            self.qDay[disease] = self.qDay[disease] - 1
            self.qFlag = True
        elif self.qDay.get(disease) and self.qDay.get(disease) == 1:
            del self.qDay[disease]
            if not bool(self.qDay):
                self.qFlag = True
            else:
                self.qFlag = False
        if self.c.get(disease) == 1: 
            if not rolldie(disease.r):
                del self.c[disease]
            else:
                self.c[disease] = -2 
            self.disease.remove(disease)
        elif self.c.get(disease) and self.c[disease] != -2: 
            self.c[disease] = self.c[disease] - 1
            return(True)
        return(False)

class Simulation():
    def __init__(self,D=500):
        self.steps = D
        self.agents = []
        self.disease = []
        self.history = []
        self.resultList = {}
        self.threadV = ()
        self.threadQ = ()

    def join(self,agent):
        self.agents.append(agent)

    def introduce(self,disease):
        self.disease.append(disease)

    def populate(self,n=2,total=10000,cp=[[.5,.2],[.2,.5]],sList=[.02,.01],qList=[.05,.07]):
        self.cp = cp
        typList = [x for x in range(n)]
        for i in range(total):
            typ = choice(typList)
            s = float(sList[typ])
            q = float(qList[typ])
            self.join(Agent(typ,s,q))

    def seed(self,disease,k=1):
        self.introduce(disease)
        for agent in sample(self.agents,k):
            agent.c[disease] = disease.E + disease.I + 1
            agent.disease.append(disease)

    def campaign(self, time, disease, coverage, v):
        self.threadV = (time,disease,coverage,v)

    def quarantine(self , time, disease, Q):
        self.threadQ = (time, disease, Q)


    def run(self):
        if not self.threadV and not self.threadQ:
            for i in self.disease:             
                for j in range(self.steps): 
                    contagious = [a for a in self.agents if a.update(i)]
                    self.history.append((len([ a for a in contagious if a.c.get(i) > i.I ]),
                                         len([ a for a in contagious if 0<a.c.get(i) <= i.I ]),
                                         len([a for a in self.agents if not a.c.get(i)])))                   
                    if self.history[-1][0:2] == (0,0): 
                        self.resultList[i.name] = self.history
                        self.history = []
                        break
                    for a1 in contagious: 
                        for a2 in self.agents:
                            if rolldie(self.cp[a1.typ][a2.typ]):
                                a2.infect(a1,i)
        
        elif self.threadV and not self.threadQ:
            for i in self.disease:
                for j in range(self.steps):
                    if j == self.threadV[0] and i.name == self.threadV[1]:
                        vPeople = [a for a in self.agents if not a.c]
                        for x in vPeople:
                            x.vaccinate(self.threadV[3],i,self.threadV[2])
                    contagious = [a for a in self.agents if a.update(i)]
                    self.history.append((len([ a for a in contagious if a.c.get(i) > i.I ]),
                                         len([ a for a in contagious if 0<a.c.get(i) <= i.I ]),
                                         len([a for a in self.agents if not a.c.get(i)])))
                    
                    if self.history[-1][0:2] == (0,0):
                        self.resultList[i.name] = self.history
                        self.history = []
                        break
                    for a1 in contagious:
                        for a2 in self.agents:
                            if rolldie(self.cp[a1.typ][a2.typ]):
                                a2.infect(a1,i)

        elif not self.threadV and self.threadQ:
            for i in self.disease:
                for j in range(self.steps):
                    if j == self.threadQ[0] and i.name == self.threadQ[1]:
                        i.quarantine(self.threadQ[2])
                    contagious = [a for a in self.agents if a.update(i)]
                    self.history.append((len([ a for a in contagious if a.c.get(i) > i.I ]),
                                         len([ a for a in contagious if 0<a.c.get(i) <= i.I ]),
                                         len([a for a in self.agents if not a.c.get(i)])))
                    
                    if self.history[-1][0:2] == (0,0):
                        self.resultList[i.name] = self.history
                        self.history = []
                        break
                    for a1 in contagious:
                        for a2 in self.agents:
                            if rolldie(self.cp[a1.typ][a2.typ]):
                                a2.infect(a1,i)
    
        elif self.threadV and self.threadQ: 
            for i in self.disease:
                for j in range(self.steps):
                    if j == self.threadQ[0] and i.name == self.threadQ[1]:
                        i.quarantine(self.threadQ[2])
                    if j == self.threadV[0] and i.name == self.threadV[1]:
                        vPeople = [a for a in self.agents if not a.c]
                        for x in vPeople:
                            x.vaccinate(self.threadV[3],i,self.threadV[2])
                    contagious = [a for a in self.agents if a.update(i)]
                    self.history.append((len([ a for a in contagious if a.c.get(i) > i.I ]),
                                         len([ a for a in contagious if 0<a.c.get(i) <= i.I ]),
                                         len([a for a in self.agents if not a.c.get(i)])))
                    
                    if self.history[-1][0:2] == (0,0):
                        self.resultList[i.name] = self.history
                        self.history = []
                        break
                    for a1 in contagious:
                        for a2 in self.agents:
                            if rolldie(self.cp[a1.typ][a2.typ]):
                                a2.infect(a1,i)
            
    def plot(self,name):
        j = self.resultList.get(name)
        plt.title(name)
        plt.axis( [0, len(j), 0, len(self.agents)] )
        plt.xlabel('Days')
        plt.ylabel('N')
        plt.plot( [ i for i in range(len(j)) ], [ e for (e, i, a) in j ],label='Exposed',color='r')
        plt.plot( [ i for i in range(len(j)) ], [ i for (e, i, a) in j ],label='Infected',color='b' )
        plt.plot( [ i for i in range(len(j)) ], [ a for (e, i, a) in j ],label='suseptible',color='g')
        plt.show()

    # Configuration function that supports interactive simulation
    def config(self):
        S = Simulation()
        pop = input("Please enter: number of groups n,number of agents,contact probability matrix among groups,suseptibility list(contains n elements),quarantine compliance probability list, seperated with a blank space \nExample: 2 500 [[.001,.001],[.001,.001]] [.99,.99] [.05,.07] \n").split(" ")
        n=int(pop[0])
        total=int(pop[1])
        cp=literal_eval(pop[2])
        sList=literal_eval(pop[3])
        qList=literal_eval(pop[4])
        S.populate(n,total,cp,sList,qList) 
        loop = 1
        dList = []
        while loop ==1:      
            seedpara = input("Please enter: fist disease's name,transmissitivity t,number of exposed days E,number of infected days I,Probability of immunity at recovery r, number of quarantine days Q, seperated with a blank space \nExample: influenza 0.95 2 7 0.8 3 \n").split(" ")
            dn = seedpara[0]
            dt = float(seedpara[1])
            de = int(seedpara[2])
            di = int(seedpara[3])
            dr = float(seedpara[4])
            dk = int(seedpara[5])
            dList.append(seedpara[0])
            S.seed(Disease(dn, dt, de, di, dr),dk)
            campaignP = input("If there's vaccination campaign for the current disease, please enter:number of days, coverage, vaccination value v. \nExample: 25 0.9 0.85 \nIf there's no campaign press enter \n").split(" ")
            try:
                if campaignP[1]:
                    ct = int(campaignP[0])
                    cc = float(campaignP[1])
                    cv = float(campaignP[2])
                    S.campaign(ct,dn,cc,cv)
            except:
                pass
            quarantineP = input("If there's quarantine order for the current disease, please enter time,and its Q.\nExample: 40 10\nIf there's no quarantine, press Enter \n").split(" ")
            try:
                if quarantineP[1]:
                    qt = int(quarantineP[0])
                    qq = int(quarantineP[1])
                    S.quarantine(qt,"mumps",qq)
            except:
                pass
            if input("Do you wish to input ohter diseases? Please enter yes or no \n").lower().startswith('n'):
                loop = 0
            else:
                loop = 1
        S.run()
        for i in dList:
            S.plot(i)
        return(S)

##s=Simulation()
##s.config()

#2 500 [[.001,.001],[.001,.001]] [.99,.99] [.05,.07]
#influenza 0.95 2 7 0.8 3
#25 0.9 0.85
#40 10
