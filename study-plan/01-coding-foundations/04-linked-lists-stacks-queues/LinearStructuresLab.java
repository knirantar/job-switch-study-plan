import java.util.*;

public final class LinearStructuresLab {
    static final class Node {
        final int value;
        Node next;
        Node(int value) { this.value = value; }
        Node(int value, Node next) { this.value = value; this.next = next; }
    }

    static Node reverse(Node head) {
        Node previous = null, current = head;
        while (current != null) {
            Node next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }
        return previous;
    }

    static Node mergeSorted(Node a, Node b) {
        Node dummy = new Node(0), tail = dummy;
        while (a != null && b != null) {
            if (a.value <= b.value) { tail.next = a; a = a.next; }
            else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = a != null ? a : b;
        return dummy.next;
    }

    static Node cycleEntry(Node head) {
        Node slow = head, fast = head;
        do {
            if (fast == null || fast.next == null) return null;
            slow = slow.next;
            fast = fast.next.next;
        } while (slow != fast);
        slow = head;
        while (slow != fast) { slow = slow.next; fast = fast.next; }
        return slow;
    }

    static boolean validBrackets(String text) {
        ArrayDeque<Character> stack = new ArrayDeque<>();
        for (char c : text.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') stack.push(c);
            else if (c == ')' || c == ']' || c == '}') {
                if (stack.isEmpty()) return false;
                char opening = stack.pop();
                if ((c == ')' && opening != '(') || (c == ']' && opening != '[') || (c == '}' && opening != '{')) return false;
            }
        }
        return stack.isEmpty();
    }

    static int[] slidingWindowMaximum(int[] values, int k) {
        if (k <= 0 || k > values.length) throw new IllegalArgumentException("invalid k");
        int[] answer = new int[values.length - k + 1];
        ArrayDeque<Integer> deque = new ArrayDeque<>();
        for (int i = 0; i < values.length; i++) {
            while (!deque.isEmpty() && deque.peekFirst() <= i - k) deque.removeFirst();
            while (!deque.isEmpty() && values[deque.peekLast()] <= values[i]) deque.removeLast();
            deque.addLast(i);
            if (i >= k - 1) answer[i - k + 1] = values[deque.peekFirst()];
        }
        return answer;
    }

    static final class TwoStackQueue<E> {
        private final ArrayDeque<E> in = new ArrayDeque<>(), out = new ArrayDeque<>();
        void add(E value) { in.push(Objects.requireNonNull(value)); }
        E remove() { moveIfNeeded(); return out.remove(); }
        E peek() { moveIfNeeded(); return out.element(); }
        boolean isEmpty() { return in.isEmpty() && out.isEmpty(); }
        private void moveIfNeeded() { if (out.isEmpty()) while (!in.isEmpty()) out.push(in.pop()); }
    }

    static final class MinStack {
        record Entry(int value, int minimum) {}
        private final ArrayDeque<Entry> entries = new ArrayDeque<>();
        void push(int value) { entries.push(new Entry(value, entries.isEmpty() ? value : Math.min(value, entries.peek().minimum()))); }
        int pop() { return entries.pop().value(); }
        int min() { return entries.element().minimum(); }
    }

    private static Node list(int... values) {
        Node dummy = new Node(0), tail = dummy;
        for (int value : values) { tail.next = new Node(value); tail = tail.next; }
        return dummy.next;
    }
    private static int[] array(Node head) {
        int[] buffer = new int[100]; int size = 0;
        for (Node n = head; n != null; n = n.next) buffer[size++] = n.value;
        return Arrays.copyOf(buffer, size);
    }
    private static void require(boolean c, String m) { if (!c) throw new AssertionError(m); }

    public static void main(String[] args) {
        require(Arrays.equals(array(reverse(list(1,2,3,4))), new int[]{4,3,2,1}), "reverse");
        require(Arrays.equals(array(mergeSorted(list(1,4,7), list(2,3,8))), new int[]{1,2,3,4,7,8}), "merge");
        Node a=list(1,2,3,4,5); Node entry=a.next.next, tail=a; while(tail.next!=null)tail=tail.next; tail.next=entry;
        require(cycleEntry(a)==entry, "cycle entry");
        require(validBrackets("payment({items:[1,2]})") && !validBrackets("([)]"), "brackets");
        require(Arrays.equals(slidingWindowMaximum(new int[]{1,3,-1,-3,5,3,6,7},3), new int[]{3,3,5,5,6,7}), "window max");
        TwoStackQueue<Integer> q=new TwoStackQueue<>(); q.add(1); q.add(2); require(q.remove()==1,"queue"); q.add(3); require(q.remove()==2,"queue order");
        MinStack ms=new MinStack(); ms.push(5); ms.push(2); ms.push(2); ms.push(7); require(ms.min()==2,"min"); ms.pop(); ms.pop(); require(ms.min()==2,"duplicate min");
        System.out.println("All linear-structures checks passed.");
    }
}
