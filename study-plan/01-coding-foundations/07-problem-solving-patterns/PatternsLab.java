import java.util.*;

public final class PatternsLab {
    static int[] sortedTwoSum(int[] a,int target){int l=0,r=a.length-1;while(l<r){long s=(long)a[l]+a[r];if(s==target)return new int[]{l,r};if(s<target)l++;else r--;}return new int[0];}
    static int longestUnique(String s){Map<Integer,Integer> last=new HashMap<>();int[] cp=s.codePoints().toArray();int left=0,best=0;for(int r=0;r<cp.length;r++){Integer p=last.put(cp[r],r);if(p!=null)left=Math.max(left,p+1);best=Math.max(best,r-left+1);}return best;}
    static long countSubarraySum(int[] a,long k){Map<Long,Long> f=new HashMap<>();f.put(0L,1L);long p=0,ans=0;for(int x:a){p+=x;ans+=f.getOrDefault(p-k,0L);f.merge(p,1L,Long::sum);}return ans;}
    static int minimumShipCapacity(int[] w,int days){int lo=0;long total=0;for(int x:w){lo=Math.max(lo,x);total+=x;}if(total>Integer.MAX_VALUE)throw new IllegalArgumentException("capacity exceeds int");int hi=(int)total;while(lo<hi){int mid=lo+(hi-lo)/2;if(canShip(w,days,mid))hi=mid;else lo=mid+1;}return lo;}
    static boolean canShip(int[] w,int days,int cap){int used=1,load=0;for(int x:w){if(load>cap-x){used++;load=0;}load+=x;}return used<=days;}
    static int[][] mergeIntervals(int[][] intervals){if(intervals.length==0)return new int[0][];int[][] copy=Arrays.stream(intervals).map(int[]::clone).toArray(int[][]::new);Arrays.sort(copy,Comparator.comparingInt(x->x[0]));List<int[]> out=new ArrayList<>();int[] current=copy[0];for(int i=1;i<copy.length;i++){if(copy[i][0]<=current[1])current[1]=Math.max(current[1],copy[i][1]);else{out.add(current);current=copy[i];}}out.add(current);return out.toArray(int[][]::new);}
    static int coinChange(int[] coins,int amount){int impossible=amount+1;int[] dp=new int[amount+1];Arrays.fill(dp,impossible);dp[0]=0;for(int value=1;value<=amount;value++)for(int coin:coins)if(coin<=value&&dp[value-coin]!=impossible)dp[value]=Math.min(dp[value],dp[value-coin]+1);return dp[amount]==impossible?-1:dp[amount];}
    static List<List<Integer>> subsetsUnique(int[] values){Arrays.sort(values);List<List<Integer>> out=new ArrayList<>();backtrack(values,0,new ArrayList<>(),out);return out;}
    static void backtrack(int[] a,int start,List<Integer> path,List<List<Integer>> out){out.add(new ArrayList<>(path));for(int i=start;i<a.length;i++){if(i>start&&a[i]==a[i-1])continue;path.add(a[i]);backtrack(a,i+1,path,out);path.remove(path.size()-1);}}
    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args){
        require(Arrays.equals(sortedTwoSum(new int[]{1,2,4,7,11},9),new int[]{1,3}),"two pointers");
        require(longestUnique("a😀b😀c")==3,"window");
        require(countSubarraySum(new int[]{3,4,7,2,-3,1,4,2},7)==4,"prefix");
        require(minimumShipCapacity(new int[]{1,2,3,4,5,6,7,8,9,10},5)==15,"answer search");
        require(Arrays.deepEquals(mergeIntervals(new int[][]{{1,3},{2,6},{8,10},{10,12}}),new int[][]{{1,6},{8,12}}),"intervals");
        require(coinChange(new int[]{1,3,4},6)==2,"dp");
        require(subsetsUnique(new int[]{1,2,2}).size()==6,"backtracking duplicates");
        System.out.println("All problem-pattern checks passed.");
    }
}
