import java.util.*;

public final class GraphsLab {
    record Edge(int to, long weight) {}
    record State(int vertex, long distance) {}

    static int[] bfsDistances(List<List<Integer>> graph, int source) {
        int[] distance = new int[graph.size()]; Arrays.fill(distance, -1);
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        distance[source] = 0; queue.add(source);
        while (!queue.isEmpty()) {
            int u = queue.remove();
            for (int v : graph.get(u)) if (distance[v] == -1) {
                distance[v] = distance[u] + 1;
                queue.add(v);
            }
        }
        return distance;
    }

    static Optional<List<Integer>> topologicalOrder(List<List<Integer>> graph) {
        int[] indegree = new int[graph.size()];
        for (List<Integer> edges : graph) for (int v : edges) indegree[v]++;
        PriorityQueue<Integer> ready = new PriorityQueue<>();
        for (int v=0;v<indegree.length;v++) if(indegree[v]==0) ready.offer(v);
        List<Integer> order=new ArrayList<>();
        while(!ready.isEmpty()) {
            int u=ready.poll(); order.add(u);
            for(int v:graph.get(u)) if(--indegree[v]==0)ready.offer(v);
        }
        return order.size()==graph.size()?Optional.of(order):Optional.empty();
    }

    static long[] dijkstra(List<List<Edge>> graph, int source) {
        long[] d=new long[graph.size()]; Arrays.fill(d,Long.MAX_VALUE); d[source]=0;
        PriorityQueue<State> pq=new PriorityQueue<>(Comparator.comparingLong(State::distance)); pq.offer(new State(source,0));
        while(!pq.isEmpty()) {
            State s=pq.poll(); if(s.distance()!=d[s.vertex()])continue;
            for(Edge e:graph.get(s.vertex())) {
                if(e.weight()<0)throw new IllegalArgumentException("negative edge");
                if(d[s.vertex()]<=Long.MAX_VALUE-e.weight()) {
                    long candidate=d[s.vertex()]+e.weight();
                    if(candidate<d[e.to()]) { d[e.to()]=candidate; pq.offer(new State(e.to(),candidate)); }
                }
            }
        }
        return d;
    }

    static final class UnionFind {
        private final int[] parent,size;
        UnionFind(int n){parent=new int[n];size=new int[n];for(int i=0;i<n;i++){parent[i]=i;size[i]=1;}}
        int find(int x){while(x!=parent[x]){parent[x]=parent[parent[x]];x=parent[x];}return x;}
        boolean union(int a,int b){int ra=find(a),rb=find(b);if(ra==rb)return false;if(size[ra]<size[rb]){int t=ra;ra=rb;rb=t;}parent[rb]=ra;size[ra]+=size[rb];return true;}
        boolean connected(int a,int b){return find(a)==find(b);}
    }

    static List<List<Integer>> graph(int n,int[][] edges,boolean directed){
        List<List<Integer>> g=new ArrayList<>();for(int i=0;i<n;i++)g.add(new ArrayList<>());
        for(int[] e:edges){g.get(e[0]).add(e[1]);if(!directed)g.get(e[1]).add(e[0]);}return g;
    }
    static List<List<Edge>> weighted(int n,long[][] edges){
        List<List<Edge>> g=new ArrayList<>();for(int i=0;i<n;i++)g.add(new ArrayList<>());
        for(long[] e:edges)g.get((int)e[0]).add(new Edge((int)e[1],e[2]));return g;
    }
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args){
        var g=graph(6,new int[][]{{0,1},{0,2},{1,3},{2,3},{3,4}},true);
        require(Arrays.equals(bfsDistances(g,0),new int[]{0,1,1,2,3,-1}),"bfs");
        require(topologicalOrder(g).orElseThrow().equals(List.of(0,1,2,3,4,5)),"topological deterministic");
        var cyclic=graph(3,new int[][]{{0,1},{1,2},{2,0}},true);require(topologicalOrder(cyclic).isEmpty(),"cycle");
        var wg=weighted(5,new long[][]{{0,1,4},{0,2,1},{2,1,2},{1,3,1},{2,3,5},{3,4,3}});
        require(Arrays.equals(dijkstra(wg,0),new long[]{0,3,1,4,7}),"dijkstra");
        UnionFind uf=new UnionFind(5);require(uf.union(0,1)&&uf.union(1,2)&&!uf.union(0,2)&&uf.connected(0,2),"union find");
        System.out.println("All graph checks passed.");
    }
}
