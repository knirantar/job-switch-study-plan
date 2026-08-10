import java.time.Instant;
import java.util.*;

public final class ModelValidationLab {
    record Money(long minorUnits,String currency){Money{if(minorUnits<=0)throw new IllegalArgumentException("positive amount required");if(!currency.matches("[A-Z]{3}"))throw new IllegalArgumentException("ISO-like currency");}}
    record PaymentKey(UUID tenant,String idempotencyKey){PaymentKey{Objects.requireNonNull(tenant);if(idempotencyKey==null||idempotencyKey.isBlank()||idempotencyKey.length()>200)throw new IllegalArgumentException();}}
    record Payment(UUID id,PaymentKey key,UUID account,Money money,Instant createdAt){Payment{Objects.requireNonNull(id);Objects.requireNonNull(key);Objects.requireNonNull(account);Objects.requireNonNull(money);Objects.requireNonNull(createdAt);}}
    static final class RepositorySimulation {
        private final Map<PaymentKey,Payment> byKey=new HashMap<>();
        synchronized Payment insert(Payment p){Payment existing=byKey.putIfAbsent(p.key(),p);if(existing!=null)throw new IllegalStateException("unique tenant/idempotency violation");return p;}
    }
    static String nextPagePredicate(){return "tenant_id = ? AND (created_at, payment_id) < (?, ?) ORDER BY created_at DESC, payment_id DESC LIMIT ?";}
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args){
        UUID tenant=UUID.randomUUID(),account=UUID.randomUUID();RepositorySimulation repo=new RepositorySimulation();PaymentKey key=new PaymentKey(tenant,"checkout-42");repo.insert(new Payment(UUID.randomUUID(),key,account,new Money(50_00,"INR"),Instant.parse("2026-08-09T10:00:00Z")));
        try{repo.insert(new Payment(UUID.randomUUID(),key,account,new Money(60_00,"INR"),Instant.now()));throw new AssertionError();}catch(IllegalStateException expected){}
        require(nextPagePredicate().contains("(created_at, payment_id) <"),"keyset tie breaker");
        System.out.println("All relational-model checks passed.");
    }
}
