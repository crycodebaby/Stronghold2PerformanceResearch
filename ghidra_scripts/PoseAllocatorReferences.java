// Read-only, exact-address reference inventory; no decompilation or database changes.
// Args: output.tsv. Known-reference completeness is not alias/writer completeness.
//@category SH2Perf
import java.io.PrintWriter;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class PoseAllocatorReferences extends GhidraScript {
    public void run() throws Exception {
        if (!currentProgram.getExecutableSHA256().equals("94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd"))
            throw new IllegalArgumentException("Unknown DLL identity");
        if (currentProgram.getImageBase().getOffset() != 0x50000000L)
            throw new IllegalArgumentException("Unexpected image base");
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("Expected output path");
        try (PrintWriter out = new PrintWriter(getScriptArgs()[0], "UTF-8")) {
            out.println("slot_va\tsource_va\ttype\tfunction_va");
            int total = 0;
            for (String slot : new String[]{"50064b48", "50064b4c"}) {
                Address target = toAddr(slot);
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(target);
                int count = 0;
                while (refs.hasNext()) {
                    monitor.checkCancelled();
                    if (++total > 4096) throw new IllegalArgumentException("Reference budget exceeded; incomplete output");
                    Reference ref = refs.next();
                    Function owner = getFunctionContaining(ref.getFromAddress());
                    out.printf("%s\t%s\t%s\t%s%n", target, ref.getFromAddress(), ref.getReferenceType(),
                        owner == null ? "-" : owner.getEntryPoint().toString());
                    count++;
                }
                out.printf("# complete_exact_references\t%s\t%d%n", target, count);
            }
            out.printf("# complete\t%d%n", total);
            if (out.checkError()) throw new java.io.IOException("Output write failed");
        }
    }
}
