// Read-only function/byte evidence for the bounded Granny pose contract.
// Usage: <output-dir> <depth> <VA>...; assembly stays in the ignored build folder.
// No decompilation, symbol changes, function creation or analysis.
//@category SH2Perf
import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;

public class PoseContract extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File dir = new File(args[0]);
        dir.mkdirs();
        int depth = Integer.parseInt(args[1]);
        LinkedHashMap<Function,Integer> queue = new LinkedHashMap<>();
        for (int i = 2; i < args.length; i++) {
            Function f = getFunctionAt(toAddr(args[i]));
            if (f == null) throw new IllegalArgumentException("Missing entry: " + args[i]);
            queue.put(f, 0);
        }
        try (PrintWriter brief = new PrintWriter(new File(dir, "functions.tsv"), "UTF-8")) {
            brief.println("sha256\t" + currentProgram.getExecutableSHA256());
            brief.println("entry\tname\tbytes\tdepth\tcallees");
            Set<Function> done = new HashSet<>();
            while (done.size() < queue.size()) {
                Function f = null;
                for (Function candidate : queue.keySet()) if (!done.contains(candidate)) { f = candidate; break; }
                done.add(f);
                int level = queue.get(f);
                Set<String> targets = new LinkedHashSet<>();
                try (PrintWriter asm = new PrintWriter(new File(dir, f.getEntryPoint() + ".txt"), "UTF-8")) {
                    for (Instruction ins : currentProgram.getListing().getInstructions(f.getBody(), true)) {
                        StringBuilder bytes = new StringBuilder();
                        for (byte b : ins.getBytes()) bytes.append(String.format("%02x", b & 255));
                        asm.println(ins.getAddress() + "\t" + bytes + "\t" + ins);
                        if (ins.getFlowType().isCall()) {
                            for (Address target : ins.getFlows()) {
                                targets.add(target.toString());
                                Function callee = getFunctionAt(target);
                                if (callee != null && level < depth && !queue.containsKey(callee)) queue.put(callee, level + 1);
                            }
                        }
                    }
                }
                brief.println(f.getEntryPoint() + "\t" + f.getName() + "\t" + f.getBody().getNumAddresses()
                              + "\t" + level + "\t" + String.join(",", targets));
                if (queue.size() > 160) throw new IllegalStateException("Export budget exceeded");
            }
        }
        println("Pose contract evidence exported; read-only; functions=" + queue.size());
    }
}
