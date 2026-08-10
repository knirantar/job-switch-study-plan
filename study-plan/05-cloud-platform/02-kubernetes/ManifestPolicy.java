import java.nio.file.*;
import java.util.*;

public final class ManifestPolicy {
  public static void main(String[] args) throws Exception {
    String y=Files.readString(Path.of(args.length==0 ? "workload.yaml" : args[0]));
    Map<String,String> required=new LinkedHashMap<>();
    required.put("image digest", "@sha256:");
    required.put("requests", "requests:");
    required.put("limits", "limits:");
    required.put("startup probe", "startupProbe:");
    required.put("readiness probe", "readinessProbe:");
    required.put("liveness probe", "livenessProbe:");
    required.put("non-root", "runAsNonRoot: true");
    required.put("no escalation", "allowPrivilegeEscalation: false");
    required.put("read-only root", "readOnlyRootFilesystem: true");
    required.put("seccomp", "seccompProfile:");
    required.put("token disabled", "automountServiceAccountToken: false");
    required.put("zone spread", "topologySpreadConstraints:");
    required.put("PDB", "kind: PodDisruptionBudget");
    required.put("HPA", "kind: HorizontalPodAutoscaler");
    required.put("network policy", "kind: NetworkPolicy");
    List<String> missing=new ArrayList<>();
    required.forEach((name,needle)->{ if(!y.contains(needle)) missing.add(name); });
    if (!missing.isEmpty()) throw new AssertionError("missing " + missing);
    if (y.contains("image: latest") || y.contains(":latest")) throw new AssertionError("mutable latest tag");
    System.out.println("Kubernetes manifest policy checks passed.");
  }
}
