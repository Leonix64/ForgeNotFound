pipeline {
    agent any 

    tools {
        jdk 'JDK 17'
    }

    stages {
        stage('Get changes') {
            steps {
                git branch: 'main', 
                    url: 'https://github.com/Leonix64/ForgeNotFound.git'
            }
        }
        
        stage('Build') {
            steps {
                sh './gradlew build --no-daemon'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'taskkill /F /IM java.exe'
                
                bat 'xcopy /Y /E /I "build\\libs\\*.jar" "C:\\ruta\\a\\tu\\servidor\\mods\\"'
                
                dir('C:\\ruta\\a\\tu\\servidor') {
                    bat 'start cmd /k "java -Xmx4G -jar forge-1.21.6-50.0.0.jar nogui"'
                }
            }
        }
    }
}