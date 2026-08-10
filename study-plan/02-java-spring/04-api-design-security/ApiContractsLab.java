import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

public final class ApiContractsLab {
    record Principal(String subject, Set<String> roles, String tenant) {}
    record PaymentCommand(String tenant, long amountCents, String currency) {}
    record Stored(String requestHash, int status, String body) {}
    record Result(int status, String body) {}
    record Problem(String type, String title, int status, String detail, String instance) {}

    static final class IdempotencyStore {
        private final Map<String, Stored> records = new HashMap<>();
        synchronized Result execute(String key, PaymentCommand command) {
            String hash = sha256(command.tenant()+"\n"+command.amountCents()+"\n"+command.currency());
            Stored existing = records.get(key);
            if (existing != null) {
                if (!MessageDigest.isEqual(existing.requestHash().getBytes(StandardCharsets.US_ASCII), hash.getBytes(StandardCharsets.US_ASCII)))
                    return new Result(409, "idempotency-key-reused-with-different-request");
                return new Result(existing.status(), existing.body());
            }
            Result created = new Result(201, "payment/" + (records.size()+1));
            records.put(key, new Stored(hash, created.status(), created.body()));
            return created;
        }
    }
    static boolean canReadPayment(Principal p,String resourceTenant,String ownerSubject){return p.tenant().equals(resourceTenant)&&(p.roles().contains("PAYMENT_ADMIN")||p.subject().equals(ownerSubject));}
    static String encodeCursor(long createdAt,long id){return Base64.getUrlEncoder().withoutPadding().encodeToString((createdAt+":"+id).getBytes(StandardCharsets.US_ASCII));}
    static long[] decodeCursor(String cursor){try{String[] parts=new String(Base64.getUrlDecoder().decode(cursor),StandardCharsets.US_ASCII).split(":",-1);if(parts.length!=2)throw new IllegalArgumentException();return new long[]{Long.parseLong(parts[0]),Long.parseLong(parts[1])};}catch(RuntimeException ex){throw new IllegalArgumentException("invalid cursor");}}
    static String sha256(String value){try{byte[] d=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));return HexFormat.of().formatHex(d);}catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}}
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args){
        IdempotencyStore store=new IdempotencyStore();var cmd=new PaymentCommand("t1",5_000,"INR");Result first=store.execute("key-1",cmd),retry=store.execute("key-1",cmd),conflict=store.execute("key-1",new PaymentCommand("t1",6_000,"INR"));
        require(first.equals(retry)&&first.status()==201&&conflict.status()==409,"idempotency");
        Principal owner=new Principal("u1",Set.of("USER"),"t1");require(canReadPayment(owner,"t1","u1")&&!canReadPayment(owner,"t1","u2")&&!canReadPayment(owner,"t2","u1"),"object authorization");
        long[] decoded=decodeCursor(encodeCursor(1_786_250_000_000L,992));require(Arrays.equals(decoded,new long[]{1_786_250_000_000L,992}),"cursor");
        System.out.println("All API-contract/security checks passed.");
    }
}
