import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 800
    height: 700
    title: "Công cụ chuyển đổi văn bản thành giọng nói"

    // Theme colors
    color: "#1e1e2e"
    
    FolderDialog {
        id: folderDialog
        title: "Chọn nơi lưu trữ"
        onAccepted: {
            outputDirField.text = folderDialog.selectedFolder.toString().replace("file:///", "")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // Save Location
        RowLayout {
            spacing: 10
            Label { text: "Thư mục lưu trữ:"; color: "#cdd6f4" }
            TextField {
                id: outputDirField
                Layout.fillWidth: true
                placeholderText: "Lựa chọn thư mục..."
                color: "#cdd6f4"
                background: Rectangle { color: "#313244"; radius: 5 }
            }
            Button {
                text: "Browse..."
                onClicked: folderDialog.open()
            }
        }

        // Filename
        RowLayout {
            spacing: 10
            Label { text: "Tên file:"; color: "#cdd6f4" }
            TextField {
                id: filenameField
                Layout.fillWidth: true
                text: "audio.wav"
                color: "#cdd6f4"
                background: Rectangle { color: "#313244"; radius: 5 }
            }
        }
        
        // Voice & Style Settings
        RowLayout {
            spacing: 20
            
            // Voice
            RowLayout {
                spacing: 10
                Label { text: "Giọng:"; color: "#cdd6f4" }
                ComboBox {
                    id: voiceComboBox
                    Layout.fillWidth: true
                    model: backend.voiceLabels
                }
            }
            
            // Style
            RowLayout {
                spacing: 10
                Label { text: "Phong cách:"; color: "#cdd6f4" }
                ComboBox {
                    id: styleComboBox
                    Layout.fillWidth: true
                    model: ["tự nhiên", "kể chuyện", "tin tức"]
                }
            }
        }

        // Text Input
        Label { text: "Văn bản:"; color: "#cdd6f4" }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                id: inputTextArea
                placeholderText: "Nhập văn bản hỗ trợ lên tới > 100.000 ký tự..."
                wrapMode: TextArea.Wrap
                color: "#cdd6f4"
                background: Rectangle { color: "#313244"; radius: 5 }
            }
        }

        // Generate Button & Status
        RowLayout {
            Button {
                id: generateButton
                text: "Tạo audio"
                enabled: !backend.isGenerating && backend.isModelLoaded
                onClicked: {
                    backend.generate_audio(
                        inputTextArea.text, 
                        outputDirField.text, 
                        filenameField.text,
                        backend.voiceVids[voiceComboBox.currentIndex],
                        styleComboBox.currentText
                    )
                }
            }
            Label {
                id: statusLabel
                text: backend.statusText
                color: backend.isGenerating ? "#f9e2af" : (backend.isModelLoaded ? "#a6e3a1" : "#f38ba8")
                Layout.fillWidth: true
                font.bold: true
            }
        }
    }
}
