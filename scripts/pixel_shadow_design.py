"""Designed anatomical shadow regions in rest coordinates, not lighting normals."""
import numpy as np

RULES = {
 'hood': 'side wedge: x > .14 + .12*(z-.65); preserve bright crown',
 'robe': 'one side panel: x > .115 + .12*(z-.30), with y > -.055',
 'sleeve': 'underside: z < .505 - .04*(abs(x-.075)-.10)',
 'scarf': 'dark teal tail; collar highlight only above z=.555',
 'legs': 'base color; dark and gold materials remain single-color',
 'coordinates': 'original Basis meters, semantic Region_ vertex groups',
 'boundary_width_m': .025,
}

def authored_shadow(obj):
 p=np.array([v.co[:] for v in obj.data.vertices]);x,y,z=p.T
 names={g.index:g.name[7:] for g in obj.vertex_groups if g.name.startswith('Region_')}
 labels=np.array([next(names[g.group] for g in v.groups if g.group in names) for v in obj.data.vertices])
 distance=np.full(len(p),-.1)  # Positive means painted shadow.
 hood=labels=='Hood';distance[hood]=np.minimum(x[hood]-(.14+.12*(z[hood]-.65)),.90-z[hood])
 robe=labels=='Robe';distance[robe]=np.minimum(x[robe]-(.115+.12*(z[robe]-.30)),y[robe]+.055)
 arms=np.char.startswith(labels,'Arm.');distance[arms]=(.505-.04*(abs(x[arms]-.075)-.10))-z[arms]
 scarf=labels=='Scarf';distance[scarf]=np.maximum(.555-z[scarf],-.005-x[scarf])
 # The existing two-color ramp switches at .18. Interpolate a narrow boundary
 # on the surface, then threshold once in the shader (no screen-space cleanup).
 field=np.clip(.18-distance/.025,-1,1).astype(np.float32)
 return field,{name:int(np.sum((labels==name)&(distance>0))) for name in np.unique(labels)}
