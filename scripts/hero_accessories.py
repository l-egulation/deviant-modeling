"""Keep the scarf/buckle and gloves coherent during larger running arm swings."""
import numpy as np

def refine_accessories(hero):
    coords=np.array([v.co[:] for v in hero.data.vertices])
    mesh=hero.data
    shader=next(n for n in hero.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    image=shader.inputs['Base Color'].links[0].from_node.image
    width,height=image.size
    pixels=np.empty(width*height*4,dtype=np.float32);image.pixels.foreach_get(pixels)
    pixels=pixels.reshape(height,width,4)
    uv=np.empty(len(mesh.loops)*2,dtype=np.float32);mesh.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
    indices=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',indices)
    xy=np.floor(uv*np.array([width,height])).astype(int)%np.array([width,height])
    rgb=np.zeros((len(coords),3),dtype=np.float32);rgb[indices]=pixels[xy[:,1],xy[:,0],:3]
    blue=(rgb[:,2]>rgb[:,0]*1.2)&(rgb[:,1]>rgb[:,0]*1.2)&(rgb[:,2]>.05)
    scarf=blue&(coords[:,2]>.52)&(coords[:,2]<.66)
    buckle=(abs(coords[:,0])<.034)&(coords[:,1]<-.11)&(coords[:,2]>.54)&(coords[:,2]<.635)
    groups={'Chest':np.flatnonzero(scarf|buckle).tolist()}
    for name,ids in groups.items():
        assert 10<len(ids)<10000,(name,len(ids))
        for group in hero.vertex_groups:
            group.remove(ids)
        hero.vertex_groups[name].add(ids,1.0,'REPLACE')
    def smooth(value,low,high):
        t=np.clip((value-low)/(high-low),0,1)
        return t*t*(3-2*t)
    # Use one continuous anatomical field for the whole sleeve. Independent
    # graph smoothing cannot preserve the source's nearly overlapping seams.
    # Distance-to-bone powers also sharpen the torso/arm boundary excessively.
    protected=set(groups['Chest'])
    arm_indices=[g.index for g in hero.vertex_groups if g.name.endswith(('Arm','ForeArm','Hand'))]
    for side,sign in [('Left',1),('Right',-1)]:
        x=coords[:,0]*sign;z=coords[:,2]
        border=.10+np.maximum(0,.535-z)*.18
        amount=smooth(x,border,border+.10)*smooth(z,.255,.30)*(1-smooth(z,.49,.545))
        glove=smooth(x,.17,.215)*smooth(z,.235,.255)*(1-smooth(z,.365,.425))
        amount=np.maximum(amount,glove)
        elbow=1-smooth(z,.39,.46)
        upper_index=hero.vertex_groups[side+'Arm'].index
        fore_index=hero.vertex_groups[side+'ForeArm'].index
        hand_index=hero.vertex_groups[side+'Hand'].index
        # Include the zero-valued boundary too, clearing the old arm influence
        # above the new shoulder field instead of leaving a hidden weight step.
        for idx in np.flatnonzero((x>.10)&(z>.23)&(z<.61)):
            if int(idx) in protected:continue
            old={g.group:g.weight for g in hero.data.vertices[int(idx)].groups if g.group not in arm_indices}
            total=sum(old.values())
            hip=1-float(smooth(z[idx],.34,.42));chest=float(smooth(z[idx],.40,.50))
            body={hero.vertex_groups['Hips'].index:hip,
                  hero.vertex_groups['Spine1'].index:(1-hip)*(1-chest),
                  hero.vertex_groups['Chest'].index:(1-hip)*chest}
            if total<1e-8:old=body;total=1
            # Old distance weights can prune every torso group on a sleeve.
            # Re-normalizing those leftovers made adjacent sleeve vertices
            # jump between hips and chest. Define torso shares continuously too.
            mix=float(smooth(z[idx],.30,.38))
            torso={i:w/total*(1-mix) for i,w in old.items()}
            for i,w in body.items():torso[i]=torso.get(i,0)+mix*w
            a=float(amount[idx]);hand=float(glove[idx]);fore=float(elbow[idx])
            values={i:w*(1-a) for i,w in torso.items()}
            values[upper_index]=a*(1-hand)*(1-fore)
            values[fore_index]=a*(1-hand)*fore
            values[hand_index]=a*hand
            for group in hero.vertex_groups:group.remove([int(idx)])
            for i,w in values.items():
                if w>1e-8:hero.vertex_groups[i].add([int(idx)],float(w),'REPLACE')
        groups[side+'Hand']=np.flatnonzero(glove>=1-1e-8).tolist()
    return {name:len(ids) for name,ids in groups.items()}
