import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class ConcurrencyBasicsLab {
    static final class SafeCounter { private final AtomicLong value=new AtomicLong(); void increment(){value.incrementAndGet();} long get(){return value.get();} }
    static final class SynchronizedAccount {
        private long cents;
        SynchronizedAccount(long cents){this.cents=cents;}
        synchronized boolean withdraw(long amount){if(amount<0)throw new IllegalArgumentException();if(cents<amount)return false;cents-=amount;return true;}
        synchronized long balance(){return cents;}
    }
    static <T> List<T> invokeBounded(List<? extends Callable<T>> tasks,int workers,int queueCapacity) throws Exception {
        ThreadPoolExecutor executor=new ThreadPoolExecutor(workers,workers,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(queueCapacity),new ThreadPoolExecutor.AbortPolicy());
        try {
            List<Future<T>> futures=new ArrayList<>();
            for(Callable<T> task:tasks)futures.add(executor.submit(task));
            List<T> results=new ArrayList<>();for(Future<T> f:futures)results.add(f.get(5,TimeUnit.SECONDS));return results;
        } finally {executor.shutdownNow();executor.awaitTermination(5,TimeUnit.SECONDS);}
    }
    static final class LockedTransfer {
        static void transfer(Account from,Account to,long cents){if(from==to)return;Account first=from.id<to.id?from:to,second=from.id<to.id?to:from;synchronized(first){synchronized(second){if(from.cents<cents)throw new IllegalStateException("insufficient");from.cents-=cents;to.cents+=cents;}}}
        static final class Account {final long id;long cents;Account(long id,long cents){this.id=id;this.cents=cents;}}
    }
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args) throws Exception {
        SafeCounter counter=new SafeCounter();int threads=8,increments=100_000;ExecutorService pool=Executors.newFixedThreadPool(threads);List<Future<?>> fs=new ArrayList<>();
        for(int t=0;t<threads;t++)fs.add(pool.submit(()->{for(int i=0;i<increments;i++)counter.increment();}));for(Future<?> f:fs)f.get();pool.shutdown();require(counter.get()==800_000,"atomic counter");
        SynchronizedAccount account=new SynchronizedAccount(1_000);ExecutorService withdrawals=Executors.newFixedThreadPool(2);Future<Boolean> a=withdrawals.submit(()->account.withdraw(700));Future<Boolean> b=withdrawals.submit(()->account.withdraw(700));require(a.get()^b.get(),"one winner");require(account.balance()==300,"invariant");withdrawals.shutdown();
        var x=new LockedTransfer.Account(1,1_000);var y=new LockedTransfer.Account(2,1_000);LockedTransfer.transfer(x,y,250);require(x.cents==750&&y.cents==1_250,"transfer");
        require(invokeBounded(List.of(()->1,()->2,()->3),2,2).equals(List.of(1,2,3)),"bounded executor");
        System.out.println("All concurrency-basics checks passed.");
    }
}
