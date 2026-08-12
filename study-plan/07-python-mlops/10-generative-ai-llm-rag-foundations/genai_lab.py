import math

def softmax(logits, temperature=1.0):
    if temperature <= 0: raise ValueError("positive temperature")
    scaled=[x/temperature for x in logits]
    maximum=max(scaled)
    exp=[math.exp(x-maximum) for x in scaled]
    total=sum(exp)
    return [x/total for x in exp]

def cosine(a,b):
    if len(a)!=len(b): raise ValueError("dimension")
    dot=sum(x*y for x,y in zip(a,b,strict=True))
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    if na==0 or nb==0: raise ValueError("zero vector")
    return dot/(na*nb)

def retrieval_budget(window, output, system_tools, history, safety):
    result=window-output-system_tools-history-safety
    if result<0: raise ValueError("context overflow")
    return result

p=softmax([2,1,0])
assert all(math.isclose(a,b,rel_tol=1e-3) for a,b in zip(p,[.6652,.2447,.09]))
hot=softmax([2,1,0],2)
assert hot[0]<p[0] and hot[2]>p[2]
assert math.isclose(cosine([1,1],[2,2]),1)
assert math.isclose(cosine([1,1],[1,-1]),0,abs_tol=1e-12)
assert retrieval_budget(16_384,1_500,1_200,1_684,0)==12_000
assert retrieval_budget(32_000,2_000,2_000,4_000,1_000)==23_000
assert (8_000**2)/(2_000**2)==16

queries=100; relevant_in_top5=82; retrieved=queries*5; judged_relevant=120
assert relevant_in_top5/queries==.82 and judged_relevant/retrieved==.24
print("PASS: stable softmax, temperature, cosine, context budget, attention growth, and retrieval metrics")
