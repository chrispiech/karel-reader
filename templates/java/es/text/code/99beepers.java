/*
 * Archivo: ColocarMuchosConos.java
 * -------------------------------
 * Puestos 42 conos usando un ciclo for
 */
import stanford.karel.*;
public class ColocarMuchosConos extends Karel {
   public void run() {
      moverse();
      /* repite ponerCono muchas veces */
      for(int i = 0; i < 42; i++) {
      	ponerCono();
      }
      moverse();
   } 
}