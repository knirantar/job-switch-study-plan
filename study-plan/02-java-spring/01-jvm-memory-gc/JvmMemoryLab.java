import java.lang.ref.*;
import java.nio.ByteBuffer;
import java.util.*;

public final class JvmMemoryLab {
    static final class Payload { final byte[] bytes; Payload(int size){bytes=new byte[size];} }
    static long allocateShortLived(int batches,int objects,int bytes){long checksum=0;for(int b=0;b<batches;b++){List<Payload> batch=new ArrayList<>(objects);for(int i=0;i<objects;i++)batch.add(new Payload(bytes));checksum+=batch.get(objects-1).bytes.length;}return checksum;}
    static boolean weakReferenceClearedEventually() throws InterruptedException {
        Object value=new byte[4*1024*1024];WeakReference<Object> ref=new WeakReference<>(value);value=null;
        for(int i=0;i<30&&ref.get()!=null;i++){System.gc();byte[][] pressure=new byte[8][];for(int j=0;j<pressure.length;j++)pressure[j]=new byte[512*1024];Thread.sleep(10);}return ref.get()==null;
    }
    static int retainedCacheEntries(int entries,int bytes){Map<Integer,Payload> cache=new HashMap<>();for(int i=0;i<entries;i++)cache.put(i,new Payload(bytes));return cache.size();}
    static int directBufferRoundTrip(){ByteBuffer b=ByteBuffer.allocateDirect(1024);b.putInt(0x12345678).flip();return b.getInt();}
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception{
        require(allocateShortLived(20,2_000,256)==20L*256,"allocations");
        require(retainedCacheEntries(1_000,128)==1_000,"retention");
        require(directBufferRoundTrip()==0x12345678,"direct memory");
        boolean cleared=weakReferenceClearedEventually();
        System.out.println("Weak reference cleared during observation="+cleared+" (GC timing is intentionally nondeterministic)");
        System.out.println("All deterministic JVM-memory checks passed.");
    }
}
