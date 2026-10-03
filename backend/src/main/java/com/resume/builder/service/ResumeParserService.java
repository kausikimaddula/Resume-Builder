package com.resume.builder.service;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.extractor.XWPFWordExtractor;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.io.IOException;

@Service
public class ResumeParserService {

    public String parseResume(byte[] fileBytes, String filename) throws IOException {
        if (filename == null || filename.isEmpty()) {
            throw new IllegalArgumentException("Filename cannot be empty");
        }

        String lowercaseName = filename.toLowerCase();
        if (lowercaseName.endsWith(".pdf")) {
            return parsePdf(fileBytes);
        } else if (lowercaseName.endsWith(".docx")) {
            return parseDocx(fileBytes);
        } else if (lowercaseName.endsWith(".txt")) {
            return new String(fileBytes);
        } else {
            throw new IllegalArgumentException("Unsupported file type: only PDF, DOCX, and TXT are supported");
        }
    }

    private String parsePdf(byte[] fileBytes) throws IOException {
        try (PDDocument document = Loader.loadPDF(fileBytes)) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        } catch (Exception e) {
            throw new IOException("Failed to parse PDF document: " + e.getMessage(), e);
        }
    }

    private String parseDocx(byte[] fileBytes) throws IOException {
        try (ByteArrayInputStream bais = new ByteArrayInputStream(fileBytes);
             XWPFDocument document = new XWPFDocument(bais);
             XWPFWordExtractor extractor = new XWPFWordExtractor(document)) {
            return extractor.getText();
        } catch (Exception e) {
            throw new IOException("Failed to parse DOCX document: " + e.getMessage(), e);
        }
    }
}
