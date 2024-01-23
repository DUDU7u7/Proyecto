


/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
import java.util.Scanner;
/**
 *
 * @author dudus
 */
public class principal {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        char c;
        int d;
        Scanner sc = new Scanner(System.in);
        System.out.println("Ingrese  el tamaño de la matriz");
        d=sc.nextInt();
        sc.nextLine();
        MatrizTriangular matriz = new MatrizTriangular(d);
        System.out.println("Ingrese un caracter para llenar la matriz");
        c=sc.nextLine().charAt(0);
        matriz.insertarElementos(c);
        matriz.mostrarA();
        matriz.mostrarB();
    }    
}
