// Local, read-only instruction and reference exporter. No decompilation.
// @category IndependentAudit
import java.io.*;
import java.util.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
public class AuditPath extends GhidraScript {
  public void run() throws Exception {
    String[] a=getScriptArgs();
    File dir=new File(a[0]); dir.mkdirs();
    Set<Function> fs=new LinkedHashSet<>();
    try(PrintWriter refs=new PrintWriter(new File(dir,"references.txt"),"UTF-8")) {
      refs.println("Program="+currentProgram.getName()+" sha256="+currentProgram.getExecutableSHA256()+" imageBase="+currentProgram.getImageBase());
      for(int i=1;i<a.length;i++) {
        Function f=getFunctionContaining(toAddr(a[i]));
        if(f==null){refs.println("No function at "+a[i]); continue;}
        fs.add(f);
        refs.println("ROOT "+f.getEntryPoint()+" "+f.getName()+" bytes="+f.getBody().getNumAddresses());
        for(Reference r:getReferencesTo(f.getEntryPoint())) {
          Function c=getFunctionContaining(r.getFromAddress());
          refs.println("REF "+r.getFromAddress()+" "+r.getReferenceType()+" caller="+(c==null?"data":c.getEntryPoint()));
          if(c!=null) fs.add(c);
        }
      }
      for(Function f:fs) {
        refs.println("EXPORT "+f.getEntryPoint()+" "+f.getName()+" bytes="+f.getBody().getNumAddresses());
        try(PrintWriter out=new PrintWriter(new File(dir,f.getEntryPoint()+".asm.txt"),"UTF-8")) {
          out.println(f.getName()+" entry="+f.getEntryPoint()+" callingConvention="+f.getCallingConventionName());
          for(Instruction ins:currentProgram.getListing().getInstructions(f.getBody(),true)) {
            out.print(ins.getAddress()+" "+ins.toString());
            for(Reference r:ins.getReferencesFrom()) {
              Symbol s=getSymbolAt(r.getToAddress());
              if(s!=null)out.print(" ; "+s.getName());
            }
            out.println();
          }
        }
      }
    }
  }
}
