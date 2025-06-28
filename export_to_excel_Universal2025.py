def export_to_excel1(students_df,materials_df,committee_df,university_name_entry,college_name_entry,
                     department_name_entry,num_students_entry,stage_entry, head_of_department_entry
    ,academic_year_entry):
    import xlsxwriter
    from xlsxwriter.utility import xl_rowcol_to_cell, xl_range_abs
    import pandas as pd

#Input Data_Section#################################################
#####################################################################
# file_name1 = "../UniversalMasterSheet/names.xlsx"  # File name for the file where the Name and Gender are listed
    df = students_df
# file_name2 = "../UniversalMasterSheet/materials.units.xlsx"  # File name of material and its units are listed
    df1 = materials_df
# file_name3 = "../UniversalMasterSheet/co.names.xlsx"  # File name for the file where the Name of Exam. Committee
    df2 = committee_df


    #uni_name= str(input("# Uni_name:")) # This shuold open later_البصرة
    uni_name=university_name_entry
#coll_name= str(input("# Colleg_name:")) # This shuold open later-التربية للعلوم الصرفة
    coll_name= college_name_entry
#depart_name= str(input("# Depart_name:")) # This shuold open later الفيزياء-
    depart_name=department_name_entry
#stage= str(input("# stage:")) # This shuold open later الاولى-
    stage= stage_entry
#year= str(input("# year of study:"))# Year of study 2023-2024
    year=academic_year_entry
#N= int(input("# of Students")) # This shuold open later
    N=50
#numb_m=int(input("# of Students"))# number of topics (materials)
#coll_name= str(input("# Colleg_name:")) # This shuold open later
#print(df.Gender.head()) # Prints first 5 rows from the top along with the header in case you want to check

    ColN= 3 #Colomn Number where the inseting will start (where the name should be located so you can use ColN+1 for the Gender
    ColC= "H"

# Start adding to your code form this point
    S=3 #the starting point for students name and gender index

    workbook = xlsxwriter.Workbook('Generated_MasterSheet.xlsx')
    worksheet = workbook.add_worksheet('MasterSheet')
    worksheet1 = workbook.add_worksheet('Statistics')
    worksheet2 = workbook.add_worksheet('النتائج الورقية')

    worksheet.set_paper(8)# A3
    worksheet.set_landscape()
    worksheet.right_to_left()
    border_format = workbook.add_format({'border': 1})
    ###################################################ِ
    worksheet1.set_paper(8)  # A3
    worksheet1.set_landscape()
    worksheet1.right_to_left()
    border_format = workbook.add_format({'border': 1})
    ####################Results WorkSheet3###############################ِ
    worksheet2.set_paper(9)  # A4
    worksheet2.set_landscape()
    worksheet2.right_to_left()
    border_format = workbook.add_format({'border': 1})
    ######ADD Number of Students##############################################################
    ######ADD Number of Students##############################################################
    ##########################################################################################
    N_page =int(N/10)
    PL=50 # Page limit
    TR=int(N_page*PL)
    k = 1
    # Writing Text
    PN= 1
    S1 = 0
    q1= 0

    ##############USING OPEN XLS MODEL TO OPEN NAMES file
    for i in range(0,TR,PL) :
            num_p1=i/48 # First page in mater
        #num_p_last=N_page/50 # First page in mater

        # Write a page number (order) in Master sheet

            cell_format1 = workbook.add_format({'bold': True})
            cell_format1.set_font_size(14)
            cell_format1.set_font('Arial')
            cell_format1.set_border(1)
       ######################################################################
            worksheet.merge_range(i, 6, i, 13, " صفحة "+str(PN)+" من "+str(N_page),cell_format1)
        #####################################################################
        # Insert an image
            worksheet.insert_image(i, 15, 'index2.jpg', {'x_scale' : 0.29, 'y_scale' : 0.29})
        ###############################################################
            cell_format = workbook.add_format({'bold' : True})
            cell_format.set_font_size(12)
            cell_format.set_font('Arial')
            caption1 = 'جامعة'+str(uni_name)
            caption2 = 'كلية'+str(coll_name)
            caption3 = 'القسم:'+str(depart_name)
            caption4 = 'المرحلـــــة:'+str(stage)
            caption5 = 'الفصـــــــل : (سنوي)'
            caption6 = 'سجل الدرجات النهائية للسنة الدراسية'+str(year)

            worksheet.write_string(i, 2, caption1,cell_format)
            worksheet.write_string(i + 1, 2, caption2,cell_format)
            worksheet.write_string(i, 9+2*len(df1), caption3,cell_format)
            worksheet.write_string(i + 1, 9+2*len(df1), caption4,cell_format)
            worksheet.write_string(i + 2, 9+2*len(df1), caption5,cell_format)
            worksheet.write_string(i + 3, 6, caption6,cell_format)
        # Merging Cells
            merge_format = workbook.add_format({'align': 'right'})
        ##############################################################
        # Set the columns and rows widths.
            worksheet.set_column(0, 3*len(df1), 6)
            worksheet.set_column(0, 3 * len(df1), 3)

            worksheet.set_column('C1:C10', 30)
        #worksheet.set_column('A:AB', 6)
        #worksheet.set_column('A:AB', 3)
            worksheet.set_column('C1:C10', 30)
            worksheet.set_column('B1:B10', 5)

            worksheet1.set_column('B1:B10', 30)
            worksheet1.set_column('R1:R10', 30)

            worksheet.set_column('AB1:AB10', 6)

            worksheet.set_column(9+2*len(df1),9+2*len(df1), 30)
            worksheet.set_column(4 + 2 * len(df1), 8 + 2 * len(df1), 3)

            cell_format = workbook.add_format({'bold' : True})
            worksheet.set_row(0, 2 * len(df1), cell_format)
            worksheet.set_row(0, None, None, {'level' : 1})
        ###Start pages loops#####################################
            border_format = workbook.add_format({'border': 1})
            worksheet.conditional_format(i + 4, 1, i + 35, 9+2*len(df1), {'type' : 'no_blanks', 'format': border_format})
            worksheet.conditional_format(i + 4, 1, i + 35, 9+2*len(df1), {'type' : 'blanks', 'format': border_format})
        ####################################################################
        # Write the caption.
            format1 = workbook.add_format({'align' : 'centre'})
            worksheet.write(i + 4, 2, 'الوحدات', format1)
        #####################################
            format2 = workbook.add_format({'align' : 'centre'})
            format2.set_text_wrap()
            format2.set_border(1)

        ######################################
            cell_format = workbook.add_format({'align' : 'centre'})
            cell_format.set_rotation(90)
            worksheet.merge_range(i + 4, 1, i + 5, 1, 'التسلسل', cell_format)
            worksheet.set_row(i + 5, 40)

            worksheet1.write(5, 0, 'ت', format2)# Working in ( الاحصائيات شيت)
            worksheet1.write(5, 3+len(df1)+3, 'ت', format2)# Working in ( الاحصائيات شيت)
            worksheet1.write(5, 3+len(df1)+3, 'ت', format2)# Working in ( الاحصائيات شيت)

            worksheet.merge_range(i + 4, 3, i + 5, 3, 'الجنس', cell_format)
            worksheet1.write(5, 2, 'الجنس', format2)

        ##########################################
            format1 = workbook.add_format({'align' : 'right'})
            format1.set_diag_type()
        # set_diag_border(1)
            worksheet.write(i + 5, 2, 'اسم الطالب                                     المواضيع', format1)
            worksheet1.write(5, 1, 'اسم الطالب', format2)
            worksheet1.write(5, 3+len(df1)+4, 'اسم الطالب', format2)

        # set_number of units############################################################
            format2 = workbook.add_format({'align' : 'centre'})
            format2.set_text_wrap()
            format2.set_border(1)

            for x1, row in df1.iterrows() :
                    worksheet.merge_range(4+i, 4+2*x1,4+i, 5+2*x1, df1.units[x1], format2)
                    worksheet.merge_range(5+i, 4+2*x1,5+i, 5+2*x1, df1.material[x1], format2)
            #For 2nd WSheet
                    worksheet1.write(4 , x1+3, df1.units[x1], format2)
                    worksheet1.write(5 , x1+3, df1.material[x1], format2)
                    worksheet1.write(5 , len(df1)+5+x1+3, df1.material[x1], format2)#Material names 2nd group
                    worksheet1.write(5, 2*len(df1) + 12 + x1 + 3, df1.material[x1], format2)  # Material names 3nd group
            worksheet.merge_range(i + 4,4+2*len(df1), i + 5,4+2*len(df1), 'النتيجة', cell_format)
            worksheet1.write(5, len(df1)+3, 'النتيجة', format2)
            worksheet1.write(5, 2*len(df1) + 8, 'النتيجة', format2)
            worksheet.merge_range(i + 4,5+2*len(df1), i + 5,5+2*len(df1), 'المعدل', cell_format)
            worksheet1.write(5, len(df1)+4, 'المعدل', format2)
            worksheet1.write(5, 2*len(df1)+9, 'المعدل', format2)

            worksheet.merge_range(i + 4,6+2*len(df1), i + 5, 6+2*len(df1), 'التقدير', cell_format)
            worksheet1.write(5, len(df1)+5, 'التقدير', format2)
            worksheet1.write(5, 2*len(df1)+10, 'التقدير', format2)

            worksheet.merge_range(i + 4,7+2*len(df1), i + 5, 7+2*len(df1), 'الترتيب', cell_format)

            worksheet.merge_range(i + 4,8+2*len(df1), i + 5, 8+2*len(df1), 'المعدل المرحلة%', cell_format)

            worksheet.merge_range(i + 4,9+2*len(df1), i + 5, 9+2*len(df1), 'الملاحظات', format2)
            worksheet1.write(5, 2*len(df1)+11, 'الملاحظات', format2)
    #################################################################################################
        # Merging Cells
            merge_format2 = workbook.add_format({'align' : 'right','valign': 'vcenter'})
            merge_format2.set_rotation(90)
            q = 0
            for j in range(3 + i, 33 + i, 3):
            #for numb in range date:
                worksheet.merge_range(j + 3, 1, j + 5, 1,"", merge_format)
                worksheet.merge_range(j + 3, 2, j + 5, 2, "", merge_format)
                worksheet.merge_range(j + 3, 3, j + 5, 3, "", merge_format)
                worksheet.merge_range(j + 3, 4+2*len(df1), j + 5, 4+2*len(df1), "", merge_format)
                worksheet.merge_range(j + 3, 5+2*len(df1), j + 5, 5+2*len(df1), "", merge_format)
                worksheet.merge_range(j + 3,  6+2*len(df1), j + 5, 6+2*len(df1), "", merge_format)
                worksheet.merge_range(j + 3,  7+2*len(df1), j + 5, 7+2*len(df1), "", merge_format)
                worksheet.merge_range(j + 3, 8+2*len(df1), j + 5, 8+2*len(df1), "", merge_format)
                worksheet.merge_range(j + 3,  9+2*len(df1), j + 5, 9+2*len(df1), "", merge_format)
            # Write a formula in Worksheet
            #    formula = f'=IF(AVERAGE({column_letter}{start_row + 1}:{column_letter}{start_row + num_students}) > 50, "Pass", "Failure")'
            # Define the starting row, ending row, and step
                start_col = 4  # Column A
                end_col = 2+2*len(df1)    # Column J
                step = 2       # Steps of 2 (A, C, E, G, I)
                cell_range_steps = []
            #cell_range = xl_range_abs(j + 3, 4, j + 3, 2*len(df1))
                n = 2
                for s in range(5,4+2*len(df1),2):
                    worksheet.write_formula(j + 3, s, f'=IF({xl_rowcol_to_cell(j + 3,s-1)}>=90,"م",IF({xl_rowcol_to_cell(j + 3,s-1)}>=80,"جـ جـ",IF({xl_rowcol_to_cell(j + 3,s-1)}>=70,"جـ",IF({xl_rowcol_to_cell(j + 3,s-1)}>=60,"ط",IF({xl_rowcol_to_cell(j + 3,s-1)}>=50,"ل","ر")))))')
               # التقدير
                    worksheet.write_formula(j + 3, 6+2*len(df1), f'=IF({xl_rowcol_to_cell(j + 3,5+2*len(df1))}>=90,"امتياز",IF({xl_rowcol_to_cell(j + 3,5+2*len(df1))}>=80,"جيد جدا",IF({xl_rowcol_to_cell(j + 3,5+2*len(df1))}>=70,"جيد",IF({xl_rowcol_to_cell(j + 3,5+2*len(df1))}>=60,"متوسط",IF({xl_rowcol_to_cell(j + 3,5+2*len(df1))}>=50,"مقبول","راسب")))))',merge_format2)
                    format6 = workbook.add_format({'font_color' : '#9C0006', 'bold' : 1})
                    worksheet.conditional_format(j + 1, s - 1, j + 5, s - 1, {'type' : 'cell',
                                                                      'criteria' : '<',
                                                                      'value' : 50,
                                                                      'format' : format6})
                    worksheet.conditional_format(j + 1, s - 2, j + 5, s - 2, {'type' : 'cell',
                                                                      'criteria' : '==',
                                                                      'value' : "ر",
                                                                      'format' : format6})
               #Work in sheet2 -Group1
                    worksheet1.write(j - q - q1 + 3, s - n, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, s-1)}", format2)
                # Work in sheet2 -Group2

                    worksheet1.write_formula(j - q - q1 + 3, s - n+len(df1)+5,
                                         f'=IF({xl_rowcol_to_cell(j - q - q1 + 3, s - n)}>=90,"امتياز",IF({xl_rowcol_to_cell(j - q - q1 + 3, s - n)}>=80,"جـيد جدا",IF({xl_rowcol_to_cell(j - q - q1 + 3, s - n)}>=70,"جـيد",IF({xl_rowcol_to_cell(j - q - q1 + 3, s - n)}>=60,"متوسط",IF({xl_rowcol_to_cell(j - q - q1 + 3, s - n)}>=50,"مقبول","راسب")))))',
                                         format2)

                    worksheet1.write(j - q - q1 + 3, 2*len(df1)+8, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 4 + 2 * len(df1))}",
                                 format2)
                    worksheet1.write(j - q - q1 + 3, 2*len(df1) + 9, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 5 + 2 * len(df1))}",
                                 format2)
                    worksheet1.write(j - q - q1 + 3,2*len(df1) + 10, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 6 + 2 * len(df1))}",
                                 format2)

                # Work in sheet2 -Group3
                    worksheet1.write_formula(j-q-q1+3,s - n+2*len(df1)+12,f'=IF({xl_rowcol_to_cell(j-q-q1+ 3, s - n)} >=50,"P","F")',format2)
                    worksheet1.write_formula(j-q-q1+3,s - n+2*len(df1)+13,f'=IF(AND({xl_rowcol_to_cell(j-q-q1+ 3, s - n)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, s - n)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, 5)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, 6)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, 7)}>=50,{xl_rowcol_to_cell(j-q-q1+3,8)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, 9)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3, 10)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3,11)}>=50,{xl_rowcol_to_cell(j-q-q1+ 3,12)}>=50),"P","F")', format2)
                    n = n + 1
                for col in range(start_col, end_col + 1, step):
                    cell = xl_rowcol_to_cell(j + 3, col)
                    cell_range_steps.append(cell)
                    stepped_range = ', '.join(cell_range_steps)
                    formula_conditions = [f'{cell}>=50' for cell in cell_range_steps]
                    formula = f'=IF(AND({", ".join(formula_conditions)}), "ناجح", "راسب")'
                    worksheet.write_formula(j + 3, 4+2*len(df1),formula ,merge_format2)
                #Find the graduation  rate
            # Write data and units to the cells
                cell_range_steps = []
                for k1, col in enumerate(range(start_col, end_col , step)) :
                    cell = xl_rowcol_to_cell(j + 3, col)  # Convert the row (0) and column to a cell reference
                    unit = df1.loc[k1, 'units']
                    cell_range_steps.append((cell, unit))
                    weighted_sum_formula = ' + '.join([f'{cell}*{unit}' for cell, unit in cell_range_steps])
                    units_sum_formula = ' + '.join([str(unit) for _, unit in cell_range_steps])
                    graduation_rate_formula = f'=({weighted_sum_formula}) / ({units_sum_formula})'
            # Write the graduation rate formula to cell L3
                    worksheet.write_formula(j + 3, 5+2*len(df1), graduation_rate_formula,merge_format2)
    #Work in Sheet 2 -Group 1
                worksheet1.write(j - q - q1 + 3, len(df1)+3, f"=MasterSheet!{xl_rowcol_to_cell(j + 3 , 4+2*len(df1))}",format2)
                worksheet1.write(j - q - q1 + 3, len(df1)+4, f"=MasterSheet!{xl_rowcol_to_cell(j + 3 , 5+2*len(df1))}",format2)
                worksheet1.write(j - q - q1 + 3, len(df1)+ 5, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 6 + 2 * len(df1))}",
                             format2)
    #######################################################
                format3 = workbook.add_format({'align' : 'right'})
                format4 = workbook.add_format({'align' : 'left'})

                for x2 in range(len(df2)):
                    if x2 > len(df2) - 3 :
                       worksheet.write(i + 21 + x2, 31, str(df2.conames[x2]), format3)
                    elif len(df2) - 4 <= x2 <= len(df2) - 3 :
                        worksheet.write(i + 23 + x2, 27, str(df2.conames[x2]), format3)
                    elif len(df2) - 6 <= x2 <= len(df2) - 4 :
                        worksheet.write(i + 25 + x2, 22, str(df2.conames[x2]), format3)
                    elif len(df2) - 9 <= x2 <= len(df2) - 4 :
                        worksheet.write(i + 28 + x2, 15, str(df2.conames[x2]), format3)
                    elif len(df2) - 12 <= x2 <= len(df2) - 9 :
                        worksheet.write(i + 31 + x2, 10, str(df2.conames[x2]), format3)
                    elif len(df2) - 15 <= x2 <= len(df2) - 12 :
                        worksheet.write(i + 34 + x2, 5, str(df2.conames[x2]), format3)
                    elif len(df2) - 19 <= x2 <= len(df2) - 14 :
                        worksheet.write(i + 37 + x2, 2, str(df2.conames[x2]), format3)

                worksheet.write(i + 42, 1, '1 ', format3)
                worksheet.write(i + 42, 2,
                            ' يمثل الحقل الاول ازاء اسم الطالب درجات الدور الاول و الذي يليه الدور الثاني و الحقل الثالث الاستحقاق',
                            format3)
                worksheet.write(i + 43, 1, '2 ', format3)
                worksheet.write(i + 43, 2,
                            'يثبت ازاء اسم الطالب سنة الرسوب ويوضع خط احمر تحت اسمه وتثبت درجات المواد غير المطالب بها لنجاحه في سنة سابقة بحبر اخضر ',
                            format3)
                worksheet.write(i + 44, 1, '3 ', format3)
                worksheet.write(i + 44, 2, 'ل= مقبول ،  ط= متوسط  ،  جـ= جيد ، جـ جـ = جيد جداً  ، م =  امتياز ', format3)
            ##################################################################################
                #Working in the worksheet2-First Group#
    #######################################################################################################
                worksheet1.write(j - q - q1 + 3, 0, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 1)}",format2)
                worksheet1.write(j - q - q1 + 3, 1, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 2)}",format2)
                worksheet1.write(j - q - q1 + 3, 2, f"=MasterSheet!{xl_rowcol_to_cell(j + 3, 3)}",format2)

                format7 = workbook.add_format({'font_color' : '#9C0006', 'bold' : 1})
                worksheet1.conditional_format(j + 1, s - 1, j + 5, s - n, {'type' : 'cell',
                                                                          'criteria' : '<',
                                                                          'value' : 50,
                                                                         'format' : format7})
            #Working in the worksheet2-Second Group
            ##########################################################
                worksheet1.write(j-q-q1+ 2,  3+len(df1)+3, f"={xl_rowcol_to_cell(j-q-q1+ 2, 0)}",format2)
                worksheet1.write(j-q-q1+ 2, 3+len(df1)+4, f"={xl_rowcol_to_cell(j-q-q1+ 2, 1)}",format2)

                #Working in the worksheet2-Third Group####################
            # worksheet1.write_formula(j-q-q1+2,s+29-n,f'=IF({xl_rowcol_to_cell(j-q-q1+ 2, s - n)} >=50,"P","F")',format2)
            # worksheet1.write_formula(j-q-q1+2,41,f'=IF(AND({xl_rowcol_to_cell(j-q-q1+ 2, 3)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 4)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 5)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 6)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 7)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2,8)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 9)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2, 10)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2,11)}>=50,{xl_rowcol_to_cell(j-q-q1+ 2,12)}>=50),"P","F")', format2)
            #worksheet1.write(4, s+29-n, f"={xl_rowcol_to_cell(4, s - n)}",format2)
            #worksheet1.write(4, 41, f"={xl_rowcol_to_cell(4, 13)}",format2)
                n = n + 2
                #format = workbook.add_format()
                #format.set_pattern(1)  # This is optional when using a solid fill.
                #format.set_bg_color('green')

        #Write a student number (order) in Master sheet
                format5 = workbook.add_format({'align': 'center', 'valign' : 'vcenter'})
                worksheet.write(j + 3, 1,k, format5)

                worksheet.write(j+3, 2, df.Name[S1],format5)
                worksheet.write(j+3, 3, df.gender[S])
                k = k + 1
                S1=S1+1
                q = q + 2
        #################################################

            q1 = q1 + 40
            PN=PN+1
        ##########################################################################
        #########################Working in Thrid Worksheet RESULTS النتائج الورقية #
        #########################Working in Thrid Worksheet RESULTS النتائج الورقية #
            caption1 = 'جامعة' + str(uni_name)
            caption2 = 'كلية' + str(coll_name)
            caption3 = 'القسم:' + str(depart_name)
            caption4 = 'المرحلـــة:' + str(stage)
            caption5 = 'الدور :'
            caption66 = 'للعام الدراسي:' + str(year)
        ######################################################################################
            format6 = workbook.add_format({'align' : 'center', 'valign' : 'vcenter'})
            format6.set_text_wrap()
            format6.set_bold()
            format6.set_font_size(12)
            format6.set_font('Arial')
        ####Main Page
            worksheet2.set_column('C1:C10', 13)
            worksheet2.set_column('J1:J10', 13)
        #worksheet2.set_column('B1:B10', 13)
       # worksheet2.set_column('I1:I10', 13)
            text ='جامعة' + str(uni_name) +'\n' + 'كلية '+ str(coll_name)  +'\n' + str(depart_name)+':قسم ' +'\n'+'اللجنة الامتحانية'
            options = {'font' : {'color' : 'black', 'size' : 11},'align' : {'vertical' : 'middle', 'horizontal' : 'left'},
                   'width' : 140, 'height' : 110, 'border' : {'none' : True}}
            text1 = 'نتائج الامتحانات النهائية' +'\n' + str(year)+':العام الدراسي' +'\n'+ 'الاول:الدور' +'\n'+str(stage)+ ':المرحلة'
            options1 = {'font' : {'color' : 'black', 'size' : 11},
                    'align' : {'horizontal': 'right'}, 'width' : 160, 'height' : 130, 'border' : {'none' : True}}
            h1 = 0
            h3 = 0
            for h2 in range(0, N, 1):
            #worksheet2.write_string(h2 + h1 - h3,0, caption3, format6)
                worksheet2.insert_textbox(h2 + h1 - h3, 0, text, options)
                worksheet2.insert_textbox(h2 + h1 - h3, 7, text, options)  ####Copy Page
           # worksheet2.write_string(h2 + h1 - h3, 8, caption1, format6)
            # Insert an image
                worksheet2.insert_image(h2 + h1 - h3, 2, 'index2.jpg', {'x_scale' : 0.25, 'y_scale' : 0.25,'x_offset': 25,'y_offset': 5})
                worksheet2.insert_image(h2 + h1 - h3, 9, 'index2.jpg', {'x_scale' : 0.25, 'y_scale' : 0.25,'x_offset': 25,'y_offset': 5})  ####Copy Page
           # worksheet2.write_string(h2 + h1 - h3, 4, caption4, format6)
                worksheet2.insert_textbox(h2 + h1 - h3, 3, text1, options1)
                worksheet2.insert_textbox(h2 + h1 - h3, 10, text1, options1)  ####Copy Page
            #worksheet2.write_string(h2 + h1 - h3, 11, caption4, format6)

            ###Call Names
                worksheet2.write(h2 + h1 + 7 - h3, 1, 'اسم الطالب: ', format6)
                worksheet2.merge_range(h2 + h1 + 7 - h3, 2, h2 + h1 + 7 - h3, 3, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 1)}",
                                   format6)
            ###Copy page
                worksheet2.write(h2 + h1 + 7 - h3, 8, 'اسم الطالب: ', format6)
                worksheet2.merge_range(h2 + h1 + 7 - h3, 9, h2 + h1 + 7 - h3, 10,
                                   f"=Statistics!{xl_rowcol_to_cell(6 + h2, 1)}", format6)
            ############################
                worksheet2.write(h2 + h1 + 8 - h3, 1, 'رقم الطالب: ', format6)
                worksheet2.write(h2 + h1 + 8 - h3, 2, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 0)}", format6)
            ###Copy page
                worksheet2.write(h2 + h1 + 8 - h3, 8, 'رقم الطالب: ', format6)
                worksheet2.write(h2 + h1 + 8 - h3, 9, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 0)}", format6)

            ###Call Topics
                worksheet2.write(h2 + h1 + 10 - h3, 1, 'المادة ', format2)
                worksheet2.write(h2 + h1 + 10 - h3, 2, 'التقدير ', format2)
                worksheet2.write(h2 + h1 + 10 - h3, 8, 'المادة ', format2)  # Copy Page
                worksheet2.write(h2 + h1 + 10 - h3, 9, 'التقدير ', format2)  # Copy Page

                for m in range(0, len(df1), 1):
                    worksheet2.write(11 + m + h2 + h1 - h3, 1, f"=Statistics!{xl_rowcol_to_cell(5, 3+ m)}", format2)
                    worksheet2.write(11 + m + h2 + h1 - h3, 2, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 8+len(df1)+ m)}", format2)
                # Copy Page
                    worksheet2.write(11 + m + h2 + h1 - h3, 8, f"=Statistics!{xl_rowcol_to_cell(5, 3+ m)}", format2)
                    worksheet2.write(11 + m + h2 + h1 - h3, 9, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 8+len(df1)+ m)}", format2)

                worksheet2.write(h1 + len(df1)+11, 1, 'النتيجة: ', format6)
                worksheet2.write(h1 + len(df1)+11, 2, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2*len(df1)+8)}", format6)
                worksheet2.write(h1 + len(df1)+11, 3, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2*len(df1)+11)}", format6)# الملاحظات

                worksheet2.write(h1 + len(df1)+12, 1, 'التقدير: ', format6)
                worksheet2.write(h1 + len(df1)+12, 2, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2*len(df1)+10)}", format6)
                worksheet2.merge_range(h1 +13+len(df1)+1, 1, h1 +13+len(df1)+1, 2, 'ختم اللجنة الامتحانية', format6)

                worksheet2.merge_range(h1 +12+len(df1)+1, 3, h1 +12+len(df1)+1, 4, '.................', format6)
                worksheet2.merge_range(h1 +13+len(df1)+1, 3, h1 +13+len(df1)+1, 4, 'رئيس القسم', format6)
            # Copy Page
                worksheet2.write(h1 + len(df1)+11, 8, 'النتيجة: ', format6)
                worksheet2.write(h1 + len(df1) + 11, 9, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2 * len(df1) + 8)}", format6)
                worksheet2.write(h1 + len(df1) + 11, 10, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2 * len(df1) + 11)}",format6)  # الملاحظات

                worksheet2.write(h1 + len(df1) + 12, 8, 'التقدير: ', format6)
                worksheet2.write(h1 + len(df1) + 12, 9, f"=Statistics!{xl_rowcol_to_cell(6 + h2, 2 * len(df1) + 10)}", format6)
                worksheet2.merge_range(h1 + 13 + len(df1) + 1, 8, h1 + 13 + len(df1) + 1, 9, 'ختم اللجنة الامتحانية', format6)
                worksheet2.merge_range(h1 + 12 + len(df1) + 1, 10, h1 + 12 + len(df1) + 1, 11, '.................', format6)
                worksheet2.merge_range(h1 + 13 + len(df1) + 1, 10, h1 + 13 + len(df1) + 1, 11, 'رئيس القسم', format6)
                h1 = h1 + 30
                h3 = h3 + 1
    workbook.close()


