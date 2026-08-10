import java.util.*;

public final class TreesHeapsTriesLab {
    static final class Node {
        final int value; Node left, right;
        Node(int value) { this.value = value; }
        Node(int value, Node left, Node right) { this.value=value; this.left=left; this.right=right; }
    }

    static List<Integer> inorderIterative(Node root) {
        List<Integer> answer = new ArrayList<>();
        ArrayDeque<Node> stack = new ArrayDeque<>();
        Node current = root;
        while (current != null || !stack.isEmpty()) {
            while (current != null) { stack.push(current); current = current.left; }
            current = stack.pop(); answer.add(current.value); current = current.right;
        }
        return answer;
    }

    static boolean validBst(Node root) { return valid(root, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static boolean valid(Node n, long lower, long upper) {
        if (n == null) return true;
        return lower < n.value && n.value < upper
                && valid(n.left, lower, n.value) && valid(n.right, n.value, upper);
    }

    static Node lowestCommonAncestor(Node root, Node p, Node q) {
        if (root == null || root == p || root == q) return root;
        Node left = lowestCommonAncestor(root.left, p, q);
        Node right = lowestCommonAncestor(root.right, p, q);
        return left != null && right != null ? root : left != null ? left : right;
    }

    static List<Integer> topK(int[] values, int k) {
        if (k < 0 || k > values.length) throw new IllegalArgumentException("invalid k");
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int value : values) {
            if (heap.size() < k) heap.offer(value);
            else if (k > 0 && value > heap.peek()) { heap.poll(); heap.offer(value); }
        }
        List<Integer> answer = new ArrayList<>(heap);
        answer.sort(Comparator.reverseOrder());
        return answer;
    }

    static final class Trie {
        static final class TrieNode { final Map<Integer, TrieNode> children = new HashMap<>(); boolean terminal; }
        private final TrieNode root = new TrieNode();
        void insert(String value) {
            TrieNode node = root;
            for (int cp : value.codePoints().toArray()) node = node.children.computeIfAbsent(cp, unused -> new TrieNode());
            node.terminal = true;
        }
        boolean contains(String value) { TrieNode n=find(value); return n != null && n.terminal; }
        boolean hasPrefix(String prefix) { return find(prefix) != null; }
        private TrieNode find(String value) {
            TrieNode node=root;
            for (int cp : value.codePoints().toArray()) { node=node.children.get(cp); if(node==null)return null; }
            return node;
        }
    }

    static String serialize(Node root) {
        StringBuilder out = new StringBuilder();
        serialize(root, out); return out.toString();
    }
    private static void serialize(Node n, StringBuilder out) {
        if (n == null) { out.append("#,"); return; }
        out.append(n.value).append(','); serialize(n.left,out); serialize(n.right,out);
    }
    static Node deserialize(String encoded) {
        ArrayDeque<String> tokens = new ArrayDeque<>(Arrays.asList(encoded.split(",")));
        return deserialize(tokens);
    }
    private static Node deserialize(ArrayDeque<String> tokens) {
        String token=tokens.remove(); if(token.equals("#"))return null;
        Node n=new Node(Integer.parseInt(token)); n.left=deserialize(tokens); n.right=deserialize(tokens); return n;
    }

    private static void require(boolean c,String m){if(!c)throw new AssertionError(m);}
    public static void main(String[] args) {
        Node n2=new Node(2), n4=new Node(4), n3=new Node(3,n2,n4), n8=new Node(8), root=new Node(5,n3,n8);
        require(inorderIterative(root).equals(List.of(2,3,4,5,8)),"inorder");
        require(validBst(root),"valid bst");
        Node invalid=new Node(5,new Node(3,null,new Node(6)),new Node(8)); require(!validBst(invalid),"deep violation");
        require(lowestCommonAncestor(root,n2,n4)==n3,"lca");
        require(topK(new int[]{5,1,9,3,12,7},3).equals(List.of(12,9,7)),"topK");
        Trie trie=new Trie(); trie.insert("café"); trie.insert("cat😀"); require(trie.contains("café")&&trie.hasPrefix("cat")&&!trie.contains("cat"),"trie");
        require(serialize(deserialize(serialize(root))).equals(serialize(root)),"round trip");
        System.out.println("All trees-heaps-tries checks passed.");
    }
}
