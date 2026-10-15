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
    for side,sign in [('Left',1),('Right',-1)]:
        glove=(coords[:,0]*sign>.215)&(coords[:,2]>.255)&(coords[:,2]<.365)
        groups[side+'Hand']=np.flatnonzero(glove).tolist()
    for name,ids in groups.items():
        assert 10<len(ids)<10000,(name,len(ids))
        for group in hero.vertex_groups:
            group.remove(ids)
        hero.vertex_groups[name].add(ids,1.0,'REPLACE')
    for side,sign in [('Left',1),('Right',-1)]:
        name=side+'Hand';hand_index=hero.vertex_groups[name].index
        transition=np.flatnonzero((coords[:,0]*sign>.20)&(coords[:,2]>=.365)&(coords[:,2]<.395))
        for idx in transition:
            old={g.group:g.weight for g in hero.data.vertices[int(idx)].groups}
            t=float((coords[idx,2]-.365)/.03);factor=1-t*t*(3-2*t)
            values={i:w*(1-factor) for i,w in old.items()}
            values[hand_index]=values.get(hand_index,0)+factor
            for group in hero.vertex_groups:group.remove([int(idx)])
            total=sum(values.values())
            for i,w in values.items():
                if w>0:hero.vertex_groups[i].add([int(idx)],w/total,'REPLACE')
    return {name:len(ids) for name,ids in groups.items()}
