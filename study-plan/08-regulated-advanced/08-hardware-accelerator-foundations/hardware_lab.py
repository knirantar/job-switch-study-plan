from math import ceil

def tensor_bytes(shape, bytes_per_value):
    elements=1
    for dimension in shape: elements*=dimension
    return elements*bytes_per_value

def amdahl(parallel_fraction, parallel_speedup):
    return 1/((1-parallel_fraction)+parallel_fraction/parallel_speedup)

def roofline(peak_flops, bandwidth_bytes_s, intensity):
    return min(peak_flops,bandwidth_bytes_s*intensity)

def kv_bytes(layers,batch,sequence,kv_heads,head_dim,bytes_per_value):
    return 2*layers*batch*sequence*kv_heads*head_dim*bytes_per_value

assert tensor_bytes((64,3,224,224),4)==38_535_168
assert tensor_bytes((32,512,4096),2)==134_217_728
assert abs(amdahl(.8,8)-3.333333333333333)<1e-12
assert abs(amdahl(.95,20)-10.256410256410254)<1e-12
assert roofline(120e12,1.5e12,20)==30e12
assert roofline(80e12,2e12,15)==30e12
assert kv_bytes(32,8,4096,32,128,2)==16*1024**3
assert kv_bytes(32,8,4096,8,128,2)==4*1024**3
assert abs(80e9/1024**3-74.50580596923828)<1e-9
print("PASS: tensor bytes, Amdahl scaling, roofline bound, KV cache, and unit conversion")
