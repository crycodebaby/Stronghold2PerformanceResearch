// Read-only bounded H-record creation evidence; raw output remains local.
//@category SH2Perf
import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.LinkedHashSet;
import java.util.Set;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class hpose_creation extends GhidraScript {
    private static final String EXE_SHA =
        "f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b";
    private static final Set<Long> CREATION_IMPORTS = Set.of(0x900AACL, 0x900AB0L, 0x900AB4L);

    public void run() throws Exception {
        if (!currentProgram.getName().equals("Stronghold2.exe")
                || !EXE_SHA.equalsIgnoreCase(currentProgram.getExecutableSHA256())) {
            throw new IllegalStateException("Program identity mismatch");
        }
        String[] args = getScriptArgs();
        if (args.length < 2 || args.length > 33) {
            throw new IllegalArgumentException("Output directory and 1..32 VA arguments required");
        }
        File directory = new File(args[0]);
        if (!directory.isDirectory() && !directory.mkdirs()) {
            throw new IOException("Cannot create local output directory");
        }
        Set<Function> functions = new LinkedHashSet<>();
        int references = 0;
        try (PrintWriter output = new PrintWriter(new File(directory, "xrefs.tsv"), "UTF-8")) {
            output.println("sha256\t" + currentProgram.getExecutableSHA256());
            for (int index = 1; index < args.length; ++index) {
                Address target = toAddr(args[index]);
                ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(target);
                while (refs.hasNext()) {
                    if (++references > 10000) throw new IllegalStateException("Reference budget exceeded");
                    Reference ref = refs.next();
                    Function caller = getFunctionContaining(ref.getFromAddress());
                    output.println(args[index] + "\t" + ref.getFromAddress() + "\t"
                        + ref.getReferenceType() + "\t" + (caller == null ? "none" : caller.getEntryPoint()));
                    // Collect callers only for the three explicit IAT slots, not
                    // every caller of each selected function.
                    if (caller != null && CREATION_IMPORTS.contains(target.getOffset())) functions.add(caller);
                }
                Function direct = getFunctionAt(target);
                if (direct != null) functions.add(direct);
                if (functions.size() > 32) throw new IllegalStateException("Function budget exceeded");
            }
            if (output.checkError()) throw new IOException("Cannot write references");
        }
        int instructions = 0;
        for (Function function : functions) {
            File path = new File(directory, function.getEntryPoint() + ".txt");
            try (PrintWriter output = new PrintWriter(path, "UTF-8")) {
                for (Instruction ins : currentProgram.getListing().getInstructions(function.getBody(), true)) {
                    if (++instructions > 50000) throw new IllegalStateException("Instruction budget exceeded");
                    StringBuilder bytes = new StringBuilder();
                    for (byte value : ins.getBytes()) bytes.append(String.format("%02x", value & 255));
                    output.println(ins.getAddress() + "\t" + bytes + "\t" + ins);
                }
                if (output.checkError()) throw new IOException("Cannot write function evidence");
            }
        }
        println("Identity verified; read-only functions=" + functions.size() + ", instructions=" + instructions);
    }
}
