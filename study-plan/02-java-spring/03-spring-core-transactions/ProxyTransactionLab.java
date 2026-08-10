import java.lang.reflect.*;
import java.util.*;

public final class ProxyTransactionLab {
    interface PaymentService { void outer(); void inner(); }
    static final class PaymentServiceImpl implements PaymentService {
        private final List<String> events;
        PaymentServiceImpl(List<String> events){this.events=events;}
        public void outer(){events.add("target.outer");this.inner();}
        public void inner(){events.add("target.inner");}
    }
    static PaymentService transactionalProxy(PaymentService target,List<String> events){
        return (PaymentService)Proxy.newProxyInstance(PaymentService.class.getClassLoader(),new Class<?>[]{PaymentService.class},(proxy,method,args)->{
            events.add("tx.begin:"+method.getName());
            try{Object result=method.invoke(target,args);events.add("tx.commit:"+method.getName());return result;}
            catch(InvocationTargetException e){events.add("tx.rollback:"+method.getName());throw e.getCause();}
        });
    }
    static final class TransactionTemplate {
        private final List<String> committed=new ArrayList<>();
        void execute(java.util.function.Consumer<List<String>> work){List<String> staged=new ArrayList<>();try{work.accept(staged);committed.addAll(staged);}catch(RuntimeException failure){/* staged discarded */throw failure;}}
        List<String> committed(){return List.copyOf(committed);}
    }
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args){
        List<String> events=new ArrayList<>();PaymentService proxy=transactionalProxy(new PaymentServiceImpl(events),events);proxy.outer();
        require(events.equals(List.of("tx.begin:outer","target.outer","target.inner","tx.commit:outer")),"self invocation should bypass proxy advice");
        proxy.inner();require(events.get(4).equals("tx.begin:inner"),"external inner intercepted");
        TransactionTemplate template=new TransactionTemplate();template.execute(staged->staged.add("payment:1"));
        try{template.execute(staged->{staged.add("payment:2");throw new IllegalStateException("fail");});}catch(IllegalStateException expected){}
        require(template.committed().equals(List.of("payment:1")),"rollback simulation");
        System.out.println("All proxy/transaction simulation checks passed.");
    }
}
