// Local coordinates: X east, Y north, Z up, meters.
function generateUniversity() {

const meshes={};
function mesh(m){return meshes[m]??= {v:[],f:[]};}
function poly(m,points){const g=mesh(m),start=g.v.length;g.v.push(...points);for(let i=1;i<points.length-1;i++)g.f.push([start,start+i,start+i+1]);}
function box(m,x,y,z,w,d,h){const p=[[x-w/2,y-d/2,z-h/2],[x+w/2,y-d/2,z-h/2],[x+w/2,y+d/2,z-h/2],[x-w/2,y+d/2,z-h/2],[x-w/2,y-d/2,z+h/2],[x+w/2,y-d/2,z+h/2],[x+w/2,y+d/2,z+h/2],[x-w/2,y+d/2,z+h/2]];for(const f of [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])poly(m,f.map(i=>p[i]));}
function beam(m,a,b,width,depth=width){let dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2],l=Math.hypot(dx,dy,dz);let u=Math.abs(dz/l)>.99?[1,0,0]:[-dy/Math.hypot(dx,dy),dx/Math.hypot(dx,dy),0];let v=[dy*u[2]-dz*u[1],dz*u[0]-dx*u[2],dx*u[1]-dy*u[0]].map(x=>x/l);let p=[];for(const c of [a,b])for(const [s,t]of [[-1,-1],[1,-1],[1,1],[-1,1]])p.push(c.map((x,i)=>x+s*u[i]*width/2+t*v[i]*depth/2));for(const f of [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])poly(m,f.map(i=>p[i]));}
function cylinder(m,x,y,z,r,h,n=16){for(let i=0;i<n;i++){let a=i*2*Math.PI/n,b=(i+1)*2*Math.PI/n,p=[x+r*Math.cos(a),y+r*Math.sin(a)],q=[x+r*Math.cos(b),y+r*Math.sin(b)];poly(m,[[...p,z],[...q,z],[...q,z+h],[...p,z+h]]);poly(m,[[x,y,z+h],[...p,z+h],[...q,z+h]]);poly(m,[[x,y,z],[...q,z],[...p,z]]);}}
function gable(m,x,y,w,d,z,rise,axis="y"){let pts=[[-w/2,-d/2,z],[w/2,-d/2,z],[0,-d/2,z+rise],[-w/2,d/2,z],[w/2,d/2,z],[0,d/2,z+rise]];if(axis==="x")pts=pts.map(p=>[p[1],p[0],p[2]]);pts=pts.map(p=>[p[0]+x,p[1]+y,p[2]]);for(const f of [[0,2,1],[3,4,5],[0,1,4,3],[0,3,5,2],[1,2,5,4]]){let pp=f.map(i=>pts[i]);if(axis!=="x")pp.reverse();poly(m==="Roof"&&f.length===3?"Brick":m,pp);}}
function roof(x,y,w,d,z,rise,axis="y"){
 gable("Roof",x,y,w,d,z,rise,axis);
 const trans=(a,b,c)=>axis==="y"?[x+a,y+b,c]:[x+b,y+a,c];
 // staggered overlapping slate rectangles follow the two roof slopes
 for(const side of [-1,1])for(let row=0;row<10;row++){
  let s0=row/10,s1=Math.min(1,(row+1.08)/10),a0=side*w/2*(1-s0),a1=side*w/2*(1-s1);
  for(let j=0;j<Math.ceil(d/.72);j++){let b0=-d/2+j*.72+(row%2)*.32,b1=Math.min(d/2,b0+.69);if(b0>=d/2)continue;
   const p=[trans(a0,b0,z+rise*s0+.035),trans(a0,b1,z+rise*s0+.035),trans(a1,b1,z+rise*s1+.035),trans(a1,b0,z+rise*s1+.035)];
   if((side===-1)===(axis==="y"))p.reverse();
   poly((row+j)%4===0?"RoofLight":"Roof",p);
  }
 }
 beam("Metal",trans(0,-d/2,z+rise+.05),trans(0,d/2,z+rise+.05),.14);
 for(const end of [-d/2,d/2])for(const side of [-1,1])beam("Stone",trans(side*w/2,end,z),trans(0,end,z+rise),.18);
}
const wings=[[-13,0,10,26],[13,0,10,26],[0,5,16,16]];
for(const [x,y,w,d]of wings){
 box("Mortar",x,y,4.5,w,d,9);
 box("StoneDark",x,y,.75,w+.12,d+.12,1.5);
 for(const z of [1.55,4.02,6.64,8.86])box("Stone",x,y,z,w+.3,d+.3,z===8.86?.34:.18);
 box("Stone",x,y,9.08,w+.65,d+.65,.22);
 // discrete brick courses on all facades, including returns in the courtyard
 for(const [axis,plane,start,end]of [["x",y-d/2,x-w/2,x+w/2],["x",y+d/2,x-w/2,x+w/2],["y",x-w/2,y-d/2,y+d/2],["y",x+w/2,y-d/2,y+d/2]]){
  for(let r=0;r<29;r++){let z=1.72+r*.24;
   for(let i=0;i<Math.ceil((end-start)/.64);i++){let a=start+i*.64+(r%2)*.32,b=Math.min(end,a+.61);if(b-a<.05)continue;
    let m=(r*7+i*13)%11<3?"BrickLight":"Brick";
    if(axis==="x")box(m,(a+b)/2,plane,z,b-a,.035,.215);else box(m,plane,(a+b)/2,z,.035,b-a,.215);
   }
  }
 }
 // alternating pale corner quoins
 for(const xx of [x-w/2,x+w/2])for(const yy of [y-d/2,y+d/2])for(let i=0;i<16;i++)box("Stone",xx,yy,1.75+i*.44,i%2?.35:.7,i%2?.7:.35,.37);
}
roof(-13,0,10.7,26.7,9.2,3.2);
roof(13,0,10.7,26.7,9.2,3.2);
roof(0,5,16.7,16.0,9.2,3.2,"x");
// brick front gables, laid over roof end faces
for(const x of [-13,13]){
 gable("Brick",x,-13.035,9.6,.12,9.2,2.88);
 beam("Stone",[x-5.25,-13.12,9.22],[x,-13.12,12.36],.22);
 beam("Stone",[x,-13.12,12.36],[x+5.25,-13.12,9.22],.22);
}
// Windows: local facade coordinates (horizontal p, outward q)
function window(x,y,z,angle,w=1.25,h=1.8){
 const C=Math.cos(angle),S=Math.sin(angle);
 function b(m,a,q,zz,ww,dd,hh){ // local cube axes horizontal and outward normal
  const g=mesh(m),begin=g.v.length;box(m,a,q,zz,ww,dd,hh);
  for(let i=begin;i<g.v.length;i++){const p=g.v[i];g.v[i]=[x+C*p[0]-S*p[1],y+S*p[0]+C*p[1],p[2]+z];}
 }
 b("Shadow",0,0,0,w+.22,.10,h+.22);
 b("Glass",0,-.07,0,w,.12,h);
 for(const a of [-w/2-.08,w/2+.08])b("Stone",a,-.13,0,.16,.22,h+.35);
 for(const zz of [-h/2-.1,h/2+.1])b("Stone",0,-.14,zz,w+.38,.28,.18);
 b("Stone",0,-.20,-h/2-.23,w+.52,.48,.13);
 for(const a of [-w/2+.035,0,w/2-.035])b("Wood",a,-.17,0,.065,.12,h);
 for(const zz of [-h/2+.035,0,h/2-.035])b("Wood",0,-.18,zz,w,.12,.065);
}
for(const x of [-13,13])for(const dx of [-3,0,3])for(const z of [.8,2.85,5.32,7.9])window(x+dx,-13.08,z,0,1.2,z===.8?.72:1.7);
for(const x of [-6,-3,0,3,6])for(const z of [2.85,5.32,7.9])if(!(x===0&&z===2.85))window(x,-3.08,z,0,1.22,1.7);
// side and rear facades
for(const side of [-1,1])for(const y of [-10,-6,-2,2,6,10])for(const z of [2.85,5.32,7.9])window(side*18.08,y,z,side===1?Math.PI/2:-Math.PI/2);
for(const side of [-1,1])for(const y of [-10,-6])for(const z of [2.85,5.32,7.9])window(side*7.94,y,z,side===1?-Math.PI/2:Math.PI/2);
for(const x of [-15,-12,-9,-6,-3,0,3,6,9,12,15])for(const z of [2.85,5.32,7.9])window(x,13.08,z,Math.PI);
// circular gable windows: ring in front plane
for(const x of [-13,13]){
 let z=10.25;
 for(let i=0;i<24;i++){let a=i*2*Math.PI/24,b=(i+1)*2*Math.PI/24;poly("Stone",[[x+.6*Math.cos(a),-13.51,z+.6*Math.sin(a)],[x+.6*Math.cos(b),-13.51,z+.6*Math.sin(b)],[x+.44*Math.cos(b),-13.51,z+.44*Math.sin(b)],[x+.44*Math.cos(a),-13.51,z+.44*Math.sin(a)]]);}
 box("Glass",x,-13.49,z,.85,.06,.85);
 beam("Wood",[x-.4,-13.54,z],[x+.4,-13.54,z],.055);
 beam("Wood",[x,-13.54,z-.4],[x,-13.54,z+.4],.055);
}
// Grand entrance and walkable six step stair.
for(let i=0;i<8;i++)box("Stone",0,-7.6+i*.40,(i+1)*.15/2,5.7,.42,(i+1)*.15);
box("Stone",0,-3.9,.6,5.7,2.7,1.2);
box("Shadow",0,-3.16,2.65,2.5,.14,2.9);
box("Door",0,-3.26,2.6,2.25,.18,2.8);
for(const side of [-1,1]){
 for(const z of [1.9,2.8,3.6])box("Wood",side*.55,-3.39,z,.81,.1,z===3.6?.45:.63);
 box("Metal",side*.12,-3.47,2.6,.055,.07,.25);
 cylinder("Stone",side*2.2,-4.55,1.2,.23,3.05);
 for(const z of [1.33,4.15])box("Stone",side*2.2,-4.55,z,.7,.7,.24);
 box("Stone",side*3,-6,.52,.42,3.6,1.04);
 box("Stone",side*3,-6,1.08,.55,3.7,.16);
}
box("Stone",0,-4.5,4.42,5.45,1.2,.36);
gable("Brick",0,-4.5,5.1,1.2,4.6,1.45);
beam("Stone",[-2.75,-5.16,4.55],[0,-5.16,6.1],.23);
beam("Stone",[0,-5.16,6.1],[2.75,-5.16,4.55],.23);
box("Stone",0,-5.14,4.60,5.6,.24,.2);
// Three central dormers and two on each wing.
function dormer(x,y,z,ang=0){
 const starts={};for(const [m,g]of Object.entries(meshes))starts[m]=g.v.length;
 box("Brick",0,0,z+.55,1.65,1.6,1.1);
 window(0,-.85,z+.55,0,.8,.85);
 roof(0,0,2.1,2, z+1.12,.8);
 for(const [m,g]of Object.entries(meshes))for(let i=starts[m]??0;i<g.v.length;i++){let [a,b,c]=g.v[i];g.v[i]=[x+a*Math.cos(ang)-b*Math.sin(ang),y+a*Math.sin(ang)+b*Math.cos(ang),c];}
}
for(const x of [-5,0,5])dormer(x,-.5,10.05);
for(const side of [-1,1])for(const y of [-6,5])dormer(side*16,y,10.0,side===1?Math.PI/2:-Math.PI/2);
// Chimneys and caps.
for(const [x,y]of [[-13,8],[13,8],[-5,7],[5,7]]){
 box("Brick",x,y,12.5,1.15,1.15,2.1);
 for(let j=0;j<5;j++)box("BrickLight",x,y,11.55+j*.38,1.18,1.18,.035);
 box("Stone",x,y,13.60,1.5,1.5,.22);
 box("Shadow",x,y,13.725,.95,.95,.04);
}
// Rain gutters and downpipes on outer corners.
for(const x of [-18.3,18.3]){
 beam("Metal",[x,-13.35,9.16],[x,13.35,9.16],.16);
 for(const y of [-12.7,12.7])cylinder("Metal",x,y,.2,.055,8.9,8);
}
// Forecourt paving and restrained planting only within university plot.
box("Paving",0,-9.5,.035,10,7,.07);
for(let x=-4.5;x<=4.5;x+=.75)box("StoneDark",x,-9.5,.078,.018,7,.012);
for(let y=-12.8;y<-6;y+=.7)box("StoneDark",0,y,.078,10,.018,.012);
for(const side of [-1,1]){
 box("Stone",side*6.25,-8.8,.20,2.1,6.5,.4);
 box("Leaf",side*6.25,-8.8,.6,1.8,6.2,.6);
 for(const y of [-11,-8.5,-6]){
  cylinder("Trunk",side*6.25,y,.4,.10,.8,8);
  for(let j=0;j<3;j++)box(j%2?"LeafLight":"Leaf",side*6.25,y,1+j*.45,1.1-j*.24,1.1-j*.24,.8);
 }
 // Lamps by stairs, total 3.5m
 const x=side*4.2,y=-9.8;
 cylinder("Metal",x,y,.05,.18,.32);
 cylinder("Metal",x,y,.3,.065,2.65,10);
 box("Metal",x,y,3.02,.5,.5,.12);
 box("Glow",x,y,3.22,.28,.28,.35);
 box("Metal",x,y,3.46,.55,.55,.14);
}
return meshes;

}

