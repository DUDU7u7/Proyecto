




/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
/**
 *
 * @author dudus
 */
public class MatrizTriangular {
    
    private char[][] elementos;

    // Constructor
    public MatrizTriangular(int d) {
        elementos = new char[d][d];
    }

    public char[][] getElementos() {
        return elementos;
    }

    public void setElementos(char[][] elementos) {
        this.elementos = elementos;
    }

    // Constructor
    public void insertarElementos(char d) {
        for (int i = 0; i < elementos.length; i++) {
            for (int j = 0; j < elementos[0].length; j++) {
                elementos[i][j] = d;
            }
        }
    }
        //Metodo para mostrar la matriz en forma del triangulo a
     public void mostrarA() {
        System.out.println("=======A=======");
        for (int i = 0; i < elementos.length; i++) { 
            for (int j = 0; j <= i; j++) {  
                System.out.print(elementos[i][j] + " "); 
            }
            System.out.println();  
        }
   
    }
     // Metodo para Mostras la matriz en forma del triangulo b
      public void mostrarB() {
        System.out.println("=======B=======");
        for (int i = 0; i < elementos.length; i++) {  
            for (int j = 0; j < elementos.length - i; j++) { 
                System.out.print(elementos[i][j] + " "); 
            }
            System.out.println();  
        }
    }
}
