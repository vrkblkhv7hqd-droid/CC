"""Generate a soft underscore with MusicGen (facebook/musicgen-small) and crossfade-loop it to the target length.
Usage: python3 tools/make-bgm.py <target_seconds> <out.wav>
"""
import sys, os, numpy as np, soundfile as sf
os.environ.setdefault('SSL_CERT_FILE','/root/.ccr/ca-bundle.crt')
target=float(sys.argv[1]); out=sys.argv[2]
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.manual_seed(7)
proc=AutoProcessor.from_pretrained('facebook/musicgen-small')
model=MusicgenForConditionalGeneration.from_pretrained('facebook/musicgen-small')
model.eval()
prompt=("calm cinematic corporate underscore, soft felt piano, warm string pads, gentle ambient texture, "
        "very light percussion, slow, hopeful, minimal, 80 bpm, background music for a narrated video")
inputs=proc(text=[prompt],padding=True,return_tensors='pt')
sr=model.config.audio_encoder.sampling_rate
seed_s=28.0
max_new=int(seed_s*50)  # 50 tokens/s
with torch.no_grad():
    audio=model.generate(**inputs,do_sample=True,guidance_scale=3.0,max_new_tokens=max_new)
a=audio[0,0].cpu().numpy().astype(np.float32)
sf.write(out.replace('.wav','-seed.wav'),a,sr)
# crossfade loop
xf=int(2.5*sr)
def loop(a,n):
    outv=a.copy()
    while len(outv)<n:
        fade=np.linspace(0,1,xf,dtype=np.float32)
        tail=outv[-xf:]*(1-fade); head=a[:xf]*fade
        outv=np.concatenate([outv[:-xf],tail+head,a[xf:]])
    return outv[:n]
n=int(target*sr)
y=loop(a,n)
# gentle normalise to -20 dBFS RMS, soft limit
rms=np.sqrt(np.mean(y**2)); y=y*(10**(-20/20)/max(rms,1e-6)); y=np.tanh(y*1.2)/1.2
fo=int(3.0*sr); y[-fo:]*=np.linspace(1,0,fo,dtype=np.float32)
fi=int(1.5*sr); y[:fi]*=np.linspace(0,1,fi,dtype=np.float32)
sf.write(out,y,sr)
print('wrote',out,len(y)/sr,'s at',sr)
