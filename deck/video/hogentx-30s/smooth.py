# objective smoothness check: per-frame change curve, flag pops (isolated spikes) and stalls
import subprocess, sys, numpy as np
f=sys.argv[1]; W,H=320,180
raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'scale={W}:{H},format=gray','-f','rawvideo','-'],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W).astype(np.float32)
d=np.abs(fr[1:]-fr[:-1]).mean(axis=(1,2))            # d[i] = change from frame i to i+1
n=len(d); print('frames',len(fr),'median change %.3f'%np.median(d))
# pops: change much larger than both neighbours' local median
pops=[]
for i in range(3,n-3):
    loc=np.median(np.r_[d[i-3:i],d[i+1:i+4]])
    if d[i]>4*loc+0.6: pops.append((i+1, d[i], loc))
print('isolated spikes (frame, change, local):')
for p in pops: print('  t=%.3fs  frame %d  %.2f vs %.2f'%(p[0]/60,p[0],p[1],p[2]))
# second difference of the change curve: jerk in overall motion energy
stall=[(i+1) for i in range(2,n-2) if d[i]<0.02 and d[i-1]>0.25 and d[i+1]>0.25]
print('stalls:',['%.3f'%(s/60) for s in stall])
# per-half-second summary
print('per 0.5s mean change:')
print(' '.join('%.1f'%d[i:i+30].mean() for i in range(0,n,30)))
np.save(f+'.diff.npy',d)
