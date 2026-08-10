import java.time.*;
import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.Predicate;

public final class TestingResilienceLab {
    interface Sleeper { void sleep(Duration duration) throws InterruptedException; }
    static <T> T retry(Callable<T> operation,int maxAttempts,Duration initial,Sleeper sleeper,Predicate<Exception> retryable) throws Exception {
        if(maxAttempts<1)throw new IllegalArgumentException();Duration delay=initial;Exception last=null;
        for(int attempt=1;attempt<=maxAttempts;attempt++)try{return operation.call();}catch(Exception e){last=e;if(attempt==maxAttempts||!retryable.test(e))throw e;sleeper.sleep(delay);delay=delay.multipliedBy(2);}
        throw last;
    }
    enum State { CLOSED, OPEN, HALF_OPEN }
    static final class CircuitBreaker {
        private final int threshold;private final Duration openFor;private final Clock clock;private State state=State.CLOSED;private int failures;private Instant openedAt;
        CircuitBreaker(int threshold,Duration openFor,Clock clock){this.threshold=threshold;this.openFor=openFor;this.clock=clock;}
        synchronized <T>T call(Callable<T> operation)throws Exception{
            if(state==State.OPEN){if(clock.instant().isBefore(openedAt.plus(openFor)))throw new IllegalStateException("circuit open");state=State.HALF_OPEN;}
            try{T result=operation.call();failures=0;state=State.CLOSED;return result;}catch(Exception e){failures++;if(state==State.HALF_OPEN||failures>=threshold){state=State.OPEN;openedAt=clock.instant();}throw e;}
        }
        synchronized State state(){return state;}
    }
    static final class MutableClock extends Clock {private Instant instant;MutableClock(Instant i){instant=i;}void advance(Duration d){instant=instant.plus(d);}public ZoneId getZone(){return ZoneOffset.UTC;}public Clock withZone(ZoneId z){return this;}public Instant instant(){return instant;}}
    static final class Account {long cents;Account(long c){cents=c;}boolean withdraw(long amount){if(amount<=0||cents<amount)return false;cents-=amount;return true;}}
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception{
        Account a=new Account(1_000);require(a.withdraw(700)&&a.cents==300&&!a.withdraw(700),"unit invariant");
        List<Duration> sleeps=new ArrayList<>();int[] attempts={0};String value=retry(()->{if(++attempts[0]<3)throw new java.io.IOException("temporary");return "ok";},3,Duration.ofMillis(100),sleeps::add,e->e instanceof java.io.IOException);require(value.equals("ok")&&sleeps.equals(List.of(Duration.ofMillis(100),Duration.ofMillis(200))),"retry");
        MutableClock clock=new MutableClock(Instant.EPOCH);CircuitBreaker cb=new CircuitBreaker(2,Duration.ofSeconds(30),clock);for(int i=0;i<2;i++)try{cb.call(()->{throw new java.io.IOException();});}catch(java.io.IOException expected){}require(cb.state()==State.OPEN,"open");try{cb.call(()->"x");throw new AssertionError();}catch(IllegalStateException expected){}clock.advance(Duration.ofSeconds(31));require(cb.call(()->"recovered").equals("recovered")&&cb.state()==State.CLOSED,"half-open recovery");
        System.out.println("All testing/resilience checks passed.");
    }
}
