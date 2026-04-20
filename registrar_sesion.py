import sqlite3

def registrar_dia():
    print("---Registro del dia:---")
    try:
        '''
        Aqui se le pregunta al usuario todos los datos necesarios para despues
        anadirlo a la base de datos y en proximos pasos crear el modelo de prediccion
        '''
        asignatura = input("Asignatura: ")
        horas_est = float(input("Horas estudiadas: "))
        nivel_conc = int(input("Nivel de concentracion de estudio (0-10)"))
        horas_sueno = float(input("Horas de sueno aproximadas"))
        hizo_ejercicio = int(input("¿Has hecho ejercicio? (1 para Si, 0 para No)"))
        nota = float(input("Puntuacion test autoevaluacion: (0-100)"))

        #Conexion base de datos
        conexion = sqlite3.connect("productividad_estudiante.db")
        #Proteccion para constraints
        conexion.execute("PRAGMA foreign_keys = ON;")
        cursor = conexion.cursor()

        #Seguridad, ? para evitar Inyeccion SQL
        sql = '''INSERT INTO sesiones_estudio
                (asignatura, horas_estudio, nivel_concentracion, horas_sueno, hizo_ejercicio, puntuacion_test) 
                VALUES (?, ?, ?, ?, ?, ?)'''
        
        #Anadir valores del usuario
        cursor.execute(sql, (asignatura, horas_est, nivel_conc, horas_sueno, hizo_ejercicio, nota))
        conexion.commit()
        print("\n✅Datos guardados exitosamente en la base de datos")
    #Manejo de errores:
    except sqlite3.IntegrityError as e:
        print("\n❌ Error de Integridad: Los datos no cumplen las reglas (Constraints). {e}")
    except ValueError:
        print("\n❌ Error: Por favor, introduce valores validos")
    except Exception as e:
        print(f"\n❌ Ocurrio un error inesperado: {e}")
    finally:
        if conexion in locals:
            conexion.close
if __name__ == "__main__":
    registrar_dia()