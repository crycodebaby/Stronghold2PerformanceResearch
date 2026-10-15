// Read-only context of addresses: containing function, previous/next function, instruction or data,
// symbol, and references TO the address (or to the containing function's entry) with their kind and the
// function / data label they come from. Addresses, names and counts only (D008).
// Headless: -postScript AddressContext.java <out.txt> <addr hex> [<addr hex> ...]
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;

import java.io.PrintWriter;

public class AddressContext extends GhidraScript {
    private String where(Address a) {
        Function f = getFunctionContaining(a);
        if (f != null) return f.getName() + "@" + f.getEntryPoint();
        Symbol s = getSymbolAt(a);
        Data d = getDataContaining(a);
        String lbl = s != null ? s.getName() : (d != null && d.getPrimarySymbol() != null ? d.getPrimarySymbol().getName() : "");
        return "no function, " + (d != null ? "data " + d.getDataType().getName() + " @" + d.getAddress() : "undefined") + (lbl.isEmpty() ? "" : " label " + lbl);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                Address a = toAddr(args[i]);
                Function f = getFunctionContaining(a);
                Instruction ins = getInstructionAt(a);
                Instruction insC = getInstructionContaining(a);
                Function prev = getFunctionBefore(a), next = getFunctionAfter(a);
                w.printf("%s: %s | instruction %s%n", a, where(a),
                    ins != null ? "starts here" : (insC != null ? "inside " + insC.getAddress() : "none"));
                if (f == null) {
                    w.printf("  prev function %s%s, next function %s%n",
                        prev != null ? prev.getName() + "@" + prev.getEntryPoint() : "-",
                        prev != null ? " (body ends " + prev.getBody().getMaxAddress() + ")" : "",
                        next != null ? next.getName() + "@" + next.getEntryPoint() : "-");
                }
                Address target = f != null ? f.getEntryPoint() : a;
                int n = 0;
                for (Reference r : getReferencesTo(target)) {
                    if (n++ >= 12) { w.println("  ..."); break; }
                    w.printf("  ref to %s from %s (%s) in %s%n", target, r.getFromAddress(), r.getReferenceType(), where(r.getFromAddress()));
                }
                if (n == 0) w.printf("  no references to %s%n", target);
            }
        }
    }
}
