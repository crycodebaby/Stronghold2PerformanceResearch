// Read-only: instruction windows around addresses (call-site argument setup) and the return instructions of
// functions (stack purge = stdcall argument bytes). Output stays under captures/ (assembly, not decompiled code, D008).
// Headless: -postScript InstructionWindow.java <out.txt> <before> <after> <addr hex>|ret:<addr hex> ...
//   <addr>      <before> instructions before and <after> after the instruction at addr, with the containing function
//   ret:<addr>  every RET in the function containing addr, its operand, and Ghidra's own convention / purge guess
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

import java.io.PrintWriter;

public class InstructionWindow extends GhidraScript {
    private String fn(Address a) {
        Function f = getFunctionContaining(a);
        return f != null ? f.getName() + "@" + f.getEntryPoint() : "no function";
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        int before = Integer.parseInt(args[1]), after = Integer.parseInt(args[2]);
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 3; i < args.length; i++) {
                if (args[i].startsWith("ret:")) {
                    Address a = toAddr(args[i].substring(4));
                    Function f = getFunctionContaining(a);
                    if (f == null) { w.printf("== ret %s: no function%n", a); continue; }
                    w.printf("== ret %s (Ghidra: convention %s, purge %d, params %d)%n", fn(a),
                        f.getCallingConventionName(), f.getStackPurgeSize(), f.getParameterCount());
                    InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                    while (it.hasNext()) {
                        Instruction ins = it.next();
                        if (ins.getMnemonicString().toUpperCase().startsWith("RET"))
                            w.printf("  %s  %s%n", ins.getAddress(), ins);
                    }
                    continue;
                }
                Address a = toAddr(args[i]);
                Instruction ins = getInstructionContaining(a);
                if (ins == null) { w.printf("== %s: no instruction%n", a); continue; }
                w.printf("== %s in %s%n", a, fn(a));
                int left = after;
                Instruction s = ins;
                for (int k = 0; k < before && s.getPrevious() != null; k++) s = s.getPrevious();
                for (Instruction c = s; c != null; c = c.getNext()) {
                    w.printf("  %s%s  %s%n", c.getAddress().equals(ins.getAddress()) ? ">" : " ", c.getAddress(), c);
                    if (c.getAddress().compareTo(ins.getAddress()) >= 0 && left-- <= 0) break;
                }
            }
        }
    }
}
