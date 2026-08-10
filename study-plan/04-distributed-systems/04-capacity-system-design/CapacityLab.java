public final class CapacityLab {
  static long peakRps(long dailyRequests, double peakToAverage) {
    if (dailyRequests < 0 || peakToAverage < 1) throw new IllegalArgumentException();
    return (long)Math.ceil(dailyRequests / 86_400.0 * peakToAverage);
  }
  static long replicas(long peakRps, double safeRpsPerReplica, int zoneFailureCapacity,
                       double growthFactor) {
    if (safeRpsPerReplica <= 0 || zoneFailureCapacity < 1 || growthFactor < 1)
      throw new IllegalArgumentException();
    long normal = (long)Math.ceil(peakRps * growthFactor / safeRpsPerReplica);
    // zoneFailureCapacity=2 means remaining two zones must carry full traffic;
    // total replicas is ceil(normal / 2 * 3) for a three-zone footprint.
    return (long)Math.ceil((double)normal / zoneFailureCapacity * (zoneFailureCapacity + 1));
  }
  static long storageBytes(long writesPerSecond, long bytesPerRecord, long retentionSeconds,
                           int copies, double overhead) {
    return (long)Math.ceil((double)writesPerSecond * bytesPerRecord * retentionSeconds * copies * overhead);
  }
  static double availabilitySerial(double... components) {
    double result=1; for (double a:components) { if(a<0||a>1) throw new IllegalArgumentException(); result*=a; }
    return result;
  }
  static double inFlight(double requestsPerSecond, double seconds) {
    return requestsPerSecond * seconds;
  }
  static double drainSeconds(long backlog, long capacityPerSecond, long arrivalsPerSecond) {
    long spare=capacityPerSecond-arrivalsPerSecond;
    return spare<=0 ? Double.POSITIVE_INFINITY : (double)backlog/spare;
  }
  public static void main(String[] args) {
    if (peakRps(86_400_000, 4) != 4_000) throw new AssertionError();
    if (replicas(4_000, 350, 2, 1.25) != 23) throw new AssertionError();
    if (storageBytes(10_000,800,86_400,3,1.2)!=2_488_320_000_000L) throw new AssertionError();
    if (Math.abs(availabilitySerial(.999,.999)-.998001)>1e-12) throw new AssertionError();
    if (inFlight(500, .2)!=100 || drainSeconds(1_800_000,1500,1000)!=3600) throw new AssertionError();
    System.out.println("Traffic, replica, storage, availability, and queue checks passed.");
  }
}
