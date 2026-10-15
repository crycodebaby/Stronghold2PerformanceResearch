// Read-only: per function, instruction count, mnemonic histogram (top 20), indirect calls/jumps with their
// operand text, and loop back edges (branch to a lower address inside the body). No decompiled code (D008).
// Headless: -postScript InstructionStats.java <out.txt> <addr hex> [...]
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.io.PrintWriter;
import java.util.*;

public class InstructionStats extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                Function f = getFunctionContaining(toAddr(args[i]));
                if (f == null) { w.printf("%s: no function%n", args[i]); continue; }
                Map<String, Integer> hist = new HashMap<>();
                List<String> indirect = new ArrayList<>(), back = new ArrayList<>();
                int n = 0;
                InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (it.hasNext()) {
                    Instruction ins = it.next();
                    n++;
                    hist.merge(ins.getMnemonicString().toLowerCase(), 1, Integer::sum);
                    if (ins.getFlowType().isComputed() && (ins.getFlowType().isCall() || ins.getFlowType().isJump()))
                        indirect.add(ins.getAddress() + " " + ins.toString());
                    for (Address t : ins.getFlows())
                        if (t.compareTo(ins.getAddress()) < 0 && f.getBody().contains(t))
                            back.add(ins.getAddress() + "->" + t);
                }
                w.printf("%s@%s: %d instructions, body %d bytes%n", f.getName(), f.getEntryPoint(), n, f.getBody().getNumAddresses());
                List<Map.Entry<String, Integer>> e = new ArrayList<>(hist.entrySet());
                e.sort((x, y) -> y.getValue() - x.getValue());
                StringBuilder sb = new StringBuilder("  mnemonics:");
                for (int k = 0; k < Math.min(20, e.size()); k++) sb.append(' ').append(e.get(k).getKey()).append('=').append(e.get(k).getValue());
                w.println(sb);
                w.println("  back edges: " + back);
                w.println("  indirect calls/jumps: " + indirect);
            }
        }
    }
}
