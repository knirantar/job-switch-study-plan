import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class VirtualThreadsLab {
    static List<Integer> virtualFanOut(int tasks, int maxDownstreamConcurrency) throws Exception {
        Semaphore permits = new Semaphore(maxDownstreamConcurrency);
        AtomicInteger active = new AtomicInteger(), observedMax = new AtomicInteger();
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<Integer>> futures = new ArrayList<>();
            for (int i = 0; i < tasks; i++) {
                final int value = i;
                futures.add(executor.submit(() -> {
                    permits.acquire();
                    try {
                        int now = active.incrementAndGet();
                        observedMax.accumulateAndGet(now, Math::max);
                        Thread.sleep(Duration.ofMillis(2));
                        return value * value;
                    } finally {
                        active.decrementAndGet();
                        permits.release();
                    }
                }));
            }
            List<Integer> results = new ArrayList<>(tasks);
            for (Future<Integer> f : futures) results.add(f.get(5, TimeUnit.SECONDS));
            if (observedMax.get() > maxDownstreamConcurrency) throw new AssertionError("bulkhead exceeded");
            return results;
        }
    }

    static int completableComposition() {
        ExecutorService io = Executors.newFixedThreadPool(4);
        try {
            CompletableFuture<Integer> price = CompletableFuture.supplyAsync(() -> 120, io);
            CompletableFuture<Integer> tax = CompletableFuture.supplyAsync(() -> 22, io);
            return price.thenCombine(tax, Integer::sum)
                    .orTimeout(2, TimeUnit.SECONDS)
                    .exceptionally(ex -> -1)
                    .join();
        } finally { io.shutdownNow(); }
    }

    static int cancellationAwareLoop() throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        CountDownLatch started = new CountDownLatch(1);
        try {
            Future<Integer> future = pool.submit(() -> {
                started.countDown();
                int completed = 0;
                try {
                    while (true) { Thread.sleep(10); completed++; }
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    return completed;
                }
            });
            started.await(); Thread.sleep(30); future.cancel(true);
            return future.isCancelled() ? 1 : 0;
        } finally { pool.shutdownNow(); pool.awaitTermination(2, TimeUnit.SECONDS); }
    }

    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        require(Thread.startVirtualThread(() -> {}).isVirtual(), "virtual thread");
        List<Integer> values = virtualFanOut(500, 12);
        require(values.size() == 500 && values.get(20) == 400, "fanout/results");
        require(completableComposition() == 142, "composition");
        require(cancellationAwareLoop() == 1, "cancellation");
        System.out.println("All virtual-thread/concurrency checks passed.");
    }
}
