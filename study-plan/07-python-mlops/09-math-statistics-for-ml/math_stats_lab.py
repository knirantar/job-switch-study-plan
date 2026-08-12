import math

def dot(a,b):
    if len(a)!=len(b): raise ValueError("shape")
    return sum(x*y for x,y in zip(a,b,strict=True))

def confusion(tp,fp,fn,tn):
    safe=lambda n,d: n/d if d else float("nan")
    precision=safe(tp,tp+fp); recall=safe(tp,tp+fn)
    return {"accuracy":safe(tp+tn,tp+fp+fn+tn), "precision":precision,
            "recall":recall, "specificity":safe(tn,tn+fp),
            "f1":safe(2*precision*recall,precision+recall)}

def bayes_counts(n, prevalence, sensitivity, specificity):
    positive=n*prevalence
    negative=n-positive
    tp=positive*sensitivity; fn=positive-tp
    tn=negative*specificity; fp=negative-tn
    return tp,fp,fn,tn

assert dot([1,2,3],[4,-1,2])==8
assert math.isclose(math.sqrt(dot([3,4],[3,4])),5)
tp,fp,fn,tn=bayes_counts(10_000,.01,.9,.95)
assert all(math.isclose(a,b) for a,b in zip((tp,fp,fn,tn),(90,495,10,9405)))
assert math.isclose(tp/(tp+fp),.15384615384615385)
m=confusion(80,20,40,860)
assert math.isclose(m["accuracy"],.94) and math.isclose(m["f1"],.7272727272727272)

w=1; x=2; y=10; learning_rate=.1
gradient=2*(w*x-y)*x
w-=learning_rate*gradient
assert math.isclose(w,4.2) and math.isclose((w*x-y)**2,2.56)

control_n=10_000; treatment_n=10_000; p1=.1; p2=.108
se=math.sqrt(p1*(1-p1)/control_n+p2*(1-p2)/treatment_n)
lower=(p2-p1)-1.96*se; upper=(p2-p1)+1.96*se
assert lower<0<upper
print("PASS: vectors, Bayes/base rate, confusion metrics, gradient step, and experiment interval")
