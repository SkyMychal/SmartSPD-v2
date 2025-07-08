# SmartSPD v2 - User Training Guide

## 🎯 Welcome to SmartSPD v2

SmartSPD v2 is your AI-powered health plan assistant designed to help TPA customer service agents provide instant, accurate answers to member questions about health benefits.

---

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [User Roles and Permissions](#user-roles-and-permissions)
3. [Document Management](#document-management)
4. [Using the AI Chat System](#using-the-ai-chat-system)
5. [Dashboard and Analytics](#dashboard-and-analytics)
6. [Admin Functions](#admin-functions)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#frequently-asked-questions)

---

## 🚀 Getting Started

### First-Time Login

1. **Access the System**
   - Navigate to your SmartSPD v2 URL
   - Use the login credentials provided by your administrator
   - If you forgot your password, contact your system administrator

2. **Initial Setup**
   - Complete your profile information
   - Review your role permissions
   - Familiarize yourself with the dashboard layout

### System Requirements

- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Internet**: Stable broadband connection
- **Resolution**: Minimum 1024x768 (responsive design supports mobile)

---

## 👥 User Roles and Permissions

### 🏢 TPA Admin
**Full system access for organization management**

**Capabilities:**
- Manage users (create, edit, deactivate)
- Upload and manage health plan documents
- View comprehensive analytics and reports  
- Configure system settings
- Access audit logs and compliance reports

**Dashboard Features:**
- System health monitoring
- User activity overview
- Document processing status
- Performance metrics

### 👨‍💼 CS Manager (Customer Service Manager)
**Supervisory access for team management**

**Capabilities:**
- Monitor team performance
- Review query analytics
- Manage document processing
- Access team reports
- View user activity

**Dashboard Features:**
- Team performance metrics
- Query success rates
- Document usage statistics
- Response time analytics

### 🎧 CS Agent (Customer Service Agent)
**Frontline access for member assistance**

**Capabilities:**
- Query health plan documents
- Access AI-powered answers
- View conversation history
- Upload new plan documents (if permitted)

**Dashboard Features:**
- Personal query statistics
- Recent conversations
- Quick document access
- Query suggestions

### 👤 Health Plan Member
**Self-service access for personal benefits**

**Capabilities:**
- Ask questions about personal benefits
- View plan documents
- Access benefit summaries
- Review coverage details

**Dashboard Features:**
- Personal benefit overview
- Recent queries
- Plan document access
- Coverage highlights

---

## 📄 Document Management

### Uploading Documents

#### Single Document Upload
1. Navigate to **Documents** → **Upload New**
2. Select your document type:
   - **SPD** (Summary Plan Description) - PDF format
   - **BPS** (Benefit Plan Specifications) - Excel format
3. Choose your file (max 50MB)
4. Enter health plan information:
   - Plan name
   - Effective date  
   - Plan identifier
5. Click **Upload**

#### Batch Document Upload
1. Go to **Documents** → **Batch Upload**
2. Select multiple files or ZIP archive
3. Configure batch settings:
   - Default document type
   - Health plan mapping
   - Processing priority
4. Click **Start Batch Upload**
5. Monitor progress in real-time

### Document Processing

**Automatic Processing Steps:**
1. **File Validation** - Format and size checks
2. **Content Extraction** - Text and table extraction
3. **AI Analysis** - Benefit structure identification
4. **Chunking** - Breaking content into searchable segments
5. **Embedding Generation** - Creating semantic search vectors
6. **Indexing** - Adding to searchable database

**Processing Times:**
- **PDF Documents**: 2-5 minutes per document
- **Excel Files**: 1-3 minutes per document
- **Large files (>10MB)**: May take 10+ minutes

### Version Management

**Creating New Versions:**
1. Go to document details page
2. Click **Upload New Version**
3. Select updated document
4. Add version notes
5. Choose activation method:
   - **Immediate** - Replace current version
   - **Scheduled** - Activate on specific date

**Version Comparison:**
- View side-by-side differences
- Track benefit changes
- Audit version history
- Rollback if needed

---

## 💬 Using the AI Chat System

### Asking Questions

#### Basic Query Structure
```
"What is my deductible for medical services?"
"How much is a copay for primary care visits?"
"Does my plan cover prescription drugs?"
```

#### Advanced Queries
```
"Compare my in-network vs out-of-network costs for specialist visits"
"What happens to my deductible if I need emergency surgery?"
"What preventive care is covered at 100% with no copay?"
```

### Query Types and Examples

#### 💰 Cost-Related Questions
- **Deductibles**: "What's my annual deductible?"
- **Copays**: "How much do I pay for urgent care?"
- **Coinsurance**: "What percentage do I pay for specialist visits?"
- **Maximums**: "What's my out-of-pocket maximum?"

#### 🏥 Coverage Questions
- **Services**: "Is physical therapy covered?"
- **Exclusions**: "What isn't covered by my plan?"
- **Limits**: "How many PT sessions per year?"
- **Authorization**: "Do I need pre-approval for MRIs?"

#### 🌐 Network Questions
- **Providers**: "How do I find in-network doctors?"
- **Referrals**: "Do I need referrals for specialists?"
- **Emergency**: "What if I need emergency care out-of-state?"

#### 💊 Prescription Coverage
- **Formulary**: "Is my medication covered?"
- **Tiers**: "What tier is my prescription?"
- **Mail Order**: "Can I use mail-order pharmacy?"
- **Generics**: "How much do generic drugs cost?"

### Understanding AI Responses

#### Response Components
1. **Direct Answer** - Clear, specific information
2. **Confidence Score** - AI certainty level (0-100%)
3. **Source Attribution** - Specific document sections
4. **Follow-up Suggestions** - Related questions to ask

#### Confidence Score Guide
- **90-100%**: High confidence, rely on answer
- **70-89%**: Good confidence, verify if critical
- **50-69%**: Moderate confidence, double-check important details
- **Below 50%**: Low confidence, manual review recommended

#### Source Verification
- Always check source documents referenced
- Look for page numbers and section titles
- Verify information matches current plan year
- Cross-reference with multiple sources when available

---

## 📊 Dashboard and Analytics

### Personal Dashboard (All Users)

#### Key Metrics
- **Queries Today**: Your daily question count
- **Average Response Time**: Speed of AI responses
- **Success Rate**: Percentage of helpful answers
- **Recent Activity**: Last 10 conversations

#### Quick Actions
- **New Query**: Start asking questions immediately
- **Recent Documents**: Access recently used plans
- **Saved Queries**: Bookmarked common questions
- **Help Center**: Training materials and support

### Manager Dashboard (CS Manager, TPA Admin)

#### Team Performance
- **Agent Activity**: Individual performance metrics
- **Query Volume**: Daily/weekly/monthly trends
- **Response Quality**: Confidence scores and feedback
- **Document Usage**: Most/least accessed plans

#### System Health
- **Processing Status**: Document upload/processing queue
- **Response Times**: System performance metrics
- **Error Rates**: Failed queries and issues
- **User Activity**: Login patterns and usage

### Analytics Reports

#### Standard Reports
- **Daily Activity Summary**: User and query statistics
- **Document Usage Report**: Plan access patterns
- **Performance Metrics**: Response times and success rates
- **Compliance Report**: Audit trail and system access

#### Custom Reports
- Filter by date range, user, or document
- Export to PDF or Excel
- Schedule automated delivery
- Share with stakeholders

---

## ⚙️ Admin Functions

### User Management

#### Creating New Users
1. Go to **Admin** → **Users** → **Add New User**
2. Fill in user information:
   - Name and email
   - Role selection
   - TPA association
   - Initial password
3. Set permissions and access levels
4. Send welcome email with login instructions

#### Managing Existing Users
- **Edit Profile**: Update user information
- **Change Role**: Modify permissions
- **Reset Password**: Generate new temporary password
- **Deactivate/Activate**: Control access without deletion
- **View Activity**: Review user query history

### System Configuration

#### Health Plan Setup
1. Navigate to **Admin** → **Health Plans**
2. Click **Add New Plan**
3. Configure plan details:
   - Plan name and identifier
   - Effective dates
   - TPA association
   - Coverage types
4. Upload initial documents
5. Test with sample queries

#### Integration Settings
- **OpenAI Configuration**: API keys and model settings
- **Database Settings**: Connection and performance tuning
- **Email Notifications**: SMTP configuration
- **Audit Settings**: Logging levels and retention

### Monitoring and Maintenance

#### System Health Checks
- **API Status**: Service availability monitoring
- **Database Performance**: Query response times
- **Storage Usage**: Document and vector storage
- **Error Monitoring**: Failed operations tracking

#### Maintenance Tasks
- **Database Cleanup**: Remove old conversations and logs
- **Document Archival**: Move inactive plans to archive
- **Performance Optimization**: Index maintenance and tuning
- **Security Updates**: System patches and upgrades

---

## 🎯 Best Practices

### For Customer Service Agents

#### Effective Querying
1. **Be Specific**: "Primary care copay" vs "doctor visit cost"
2. **Use Plan Terms**: Reference specific benefit names
3. **Ask Follow-ups**: Build on previous answers
4. **Verify Dates**: Ensure plan year accuracy

#### Quality Assurance
- Always verify AI responses with source documents
- Cross-reference important benefit information
- Document unusual or complex scenarios
- Escalate low-confidence responses to supervisors

#### Member Interaction
- Explain how you're finding the information
- Share confidence levels when appropriate  
- Provide source document references
- Offer to research further if needed

### For Managers

#### Team Training
- Regular training sessions on new features
- Share best practice examples
- Review analytics to identify training needs
- Create standard operating procedures

#### Quality Management
- Monitor response confidence trends
- Review escalated queries
- Provide feedback on query techniques
- Track improvement over time

#### Performance Optimization
- Identify frequently asked questions
- Optimize document organization
- Monitor system performance
- Plan capacity for peak usage

### For Administrators

#### Document Management
- Maintain up-to-date plan documents
- Implement version control procedures
- Regular quality audits of uploaded content
- Monitor processing performance

#### System Maintenance
- Regular backup procedures
- Monitor system performance metrics
- Plan for capacity growth
- Implement security best practices

#### User Support
- Provide comprehensive training
- Maintain help documentation
- Respond promptly to user issues
- Gather feedback for improvements

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Login Problems
**Issue**: Cannot log in to system
**Solutions**:
- Verify username/email spelling
- Try password reset
- Check browser compatibility
- Clear browser cache
- Contact administrator if account locked

#### Document Upload Failures
**Issue**: Document won't upload or process
**Solutions**:
- Check file size (max 50MB)
- Verify file format (PDF/Excel)
- Ensure stable internet connection
- Try uploading during off-peak hours
- Contact support for large files

#### Slow Query Responses
**Issue**: AI takes too long to respond
**Solutions**:
- Check internet connection speed
- Try simpler, more specific questions
- Wait for system to finish processing documents
- Report persistent issues to administrator

#### Inaccurate Answers
**Issue**: AI provides wrong information
**Solutions**:
- Check source documents directly
- Verify query wording is clear
- Look at confidence score
- Try rephrasing the question
- Report inaccuracies to improve system

#### Missing Documents
**Issue**: Cannot find expected health plan
**Solutions**:
- Check document upload status
- Verify document processing completed
- Confirm you have access permissions
- Search by different plan identifiers
- Contact administrator about missing plans

### Getting Help

#### Self-Service Options
1. **Help Center**: Built-in documentation and tutorials
2. **FAQ Section**: Common questions and answers
3. **Video Tutorials**: Step-by-step walkthroughs
4. **Knowledge Base**: Searchable help articles

#### Contacting Support
- **In-App Support**: Click help icon for immediate assistance
- **Email Support**: Send detailed issue descriptions
- **Phone Support**: For urgent issues (if available)
- **Admin Escalation**: Route through your system administrator

---

## ❓ Frequently Asked Questions

### General System Questions

**Q: How often should documents be updated?**
A: Upload new plan documents whenever benefit changes occur, typically annually during open enrollment or when amendments are issued.

**Q: Can I access the system from mobile devices?**
A: Yes, SmartSPD v2 is fully responsive and works on tablets and smartphones with modern browsers.

**Q: How secure is member health information?**
A: The system follows HIPAA compliance standards with encryption, audit logging, and role-based access controls.

**Q: What happens if the AI doesn't know an answer?**
A: The system will indicate low confidence and suggest manual research or escalation to supervisors.

### Document Management Questions

**Q: What file formats are supported?**
A: PDFs for Summary Plan Descriptions (SPDs) and Excel files (.xlsx) for Benefit Plan Specifications (BPS).

**Q: How long does document processing take?**
A: Typically 2-5 minutes for PDFs and 1-3 minutes for Excel files, depending on size and complexity.

**Q: Can I upload documents in other languages?**
A: Currently, the system is optimized for English-language documents. Contact your administrator about multilingual support.

**Q: What if I upload the wrong document version?**
A: You can upload a new version or contact your administrator to restore a previous version.

### Query and AI Questions

**Q: Why do some answers have low confidence scores?**
A: Low confidence indicates the AI found limited or conflicting information. Always verify these responses manually.

**Q: Can I save frequently asked questions?**
A: Yes, use the bookmark feature to save common queries for quick access.

**Q: How do I ask about plan comparisons?**
A: Frame questions like "Compare deductibles between Plan A and Plan B" or "What are the differences in prescription coverage?"

**Q: What if I disagree with an AI answer?**
A: Always verify with source documents and report inaccuracies to help improve the system.

### Technical Questions

**Q: Why is the system slow?**
A: Possible causes include high system usage, large document processing, or internet connectivity issues.

**Q: Can I use SmartSPD offline?**
A: No, the system requires internet connectivity to access AI services and document databases.

**Q: How do I clear my query history?**
A: Contact your administrator about data retention policies and history management options.

**Q: What browsers work best?**
A: Chrome, Firefox, Safari, and Edge (latest versions) are fully supported.

---

## 📞 Support and Resources

### Training Resources
- **Video Library**: Step-by-step tutorials for all features
- **Webinar Schedule**: Live training sessions and Q&A
- **Practice Environment**: Safe space to test queries
- **Certification Program**: Structured learning path

### Documentation
- **User Manual**: Comprehensive feature documentation
- **API Documentation**: For technical integrations
- **Administrator Guide**: System configuration and management
- **Release Notes**: New features and updates

### Community and Support
- **User Forum**: Community discussions and tips
- **Best Practices Sharing**: Success stories and techniques
- **Feature Requests**: Submit ideas for improvements
- **Bug Reports**: Report issues for faster resolution

---

## 🎓 Getting the Most from SmartSPD v2

### Success Tips
1. **Start Simple**: Begin with basic queries and build complexity
2. **Use Specific Terms**: Reference exact benefit names and plan terminology
3. **Verify Important Information**: Always check source documents for critical details
4. **Provide Feedback**: Help improve the system by reporting issues and suggestions
5. **Stay Updated**: Regularly check for new features and training materials

### Advanced Techniques
- **Query Chaining**: Build on previous answers with follow-up questions
- **Context Setting**: Specify member situations for more accurate responses
- **Comparison Queries**: Ask for side-by-side benefit comparisons
- **Scenario Testing**: Explore hypothetical situations and outcomes

### Measuring Success
- **Response Accuracy**: Verify answers match plan documents
- **Time Savings**: Track efficiency improvements in member interactions
- **Member Satisfaction**: Monitor feedback and resolution rates
- **Knowledge Growth**: Build expertise through regular system use

---

**Ready to get started? Log in to SmartSPD v2 and begin exploring your AI-powered health plan assistant!**

---

*Last Updated: July 2025*  
*Version: 2.0*  
*Contact: Your System Administrator*