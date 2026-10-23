"""Small deterministic distance-constraint cloth solver in world space.
Pinned attachments, gravity, air drag, capsule contacts and cloth contact.
This is offline physics, not a sine-wave animation or a game-engine component.
"""
import numpy as np

class Cloth:
 def __init__(self,rest,rows,cols,pins,drag):
  self.x=rest.copy();self.v=np.zeros_like(rest);self.inv=np.ones(len(rest));self.inv[pins]=0;self.pins=np.array(pins);self.drag=drag
  self.edges=[]
  for di,dj,compliance in [(1,0,1e-7),(0,1,1e-7),(1,1,3e-7),(1,-1,3e-7),(2,0,2e-4),(0,2,2e-4)]:
   for parity in range(3):
    pairs=[]
    for i in range(rows):
     for j in range(cols):
      ii,jj=i+di,j+dj
      if 0<=ii<rows and 0<=jj<cols and (i if di else j)%3==parity:pairs.append((i*cols+j,ii*cols+jj))
    e=np.array(pairs,dtype=int)
    if len(e):self.edges.append((e,np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1),compliance))
  self.rows=rows;self.cols=cols;self.previous_attachment=rest.copy()
 def step(self,attachment,capsules,cloth_contact=None):
  dt=1/240
  for sub in range(8):
   old=self.x.copy();self.v+=(np.array([0,0,-9.81])-self.drag*self.v)*dt
   pins=(self.previous_attachment+(attachment-self.previous_attachment)*(sub+1)/8)[self.pins]
   self.x+=self.v*dt;self.x[self.pins]=pins
   for iteration in range(12):
    for e,rest,compliance in self.edges:
     a,b=e.T;delta=self.x[b]-self.x[a];length=np.maximum(np.linalg.norm(delta,axis=1),1e-9)
     denom=self.inv[a]+self.inv[b]+compliance/(dt*dt);correction=delta*((length-rest)/length/denom)[:,None]
     # Jacobi accumulation avoids order-dependent duplicate-index writes.
     accum=np.zeros_like(self.x);counts=np.zeros(len(self.x))
     np.add.at(accum,a,correction*self.inv[a,None]);np.add.at(accum,b,-correction*self.inv[b,None])
     np.add.at(counts,a,1);np.add.at(counts,b,1)
     self.x+=accum/np.maximum(counts[:,None],1)
    for start,end,radius in capsules:
     ab=end-start;t=np.clip(((self.x-start)@ab)/max(float(ab@ab),1e-9),0,1)
     center=start+t[:,None]*ab;delta=self.x-center;length=np.linalg.norm(delta,axis=1)
     hit=(length<radius)&(self.inv>0)
     self.x[hit]=center[hit]+delta[hit]/np.maximum(length[hit,None],1e-8)*radius
    self.x[self.inv>0,2]=np.maximum(self.x[self.inv>0,2],.012)
    self.x[self.pins]=pins
   if cloth_contact is not None:self.x=cloth_contact(self.x,self.inv)
   self.v=(self.x-old)/dt;self.v[self.pins]=0
   assert np.isfinite(self.x).all()
  self.previous_attachment=attachment.copy()
  return self.x.copy()

def grid_binding(u,v,rows,cols):
 a=np.clip(u*(rows-1),0,rows-1-1e-7);b=np.clip(v*(cols-1),0,cols-1-1e-7)
 i=np.floor(a).astype(int);j=np.floor(b).astype(int);s=a-i;t=b-j
 return np.stack([i*cols+j,(i+1)*cols+j,i*cols+j+1,(i+1)*cols+j+1],axis=1),np.stack([(1-s)*(1-t),s*(1-t),(1-s)*t,s*t],axis=1)
